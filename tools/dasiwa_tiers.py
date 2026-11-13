"""Auto size from the input image + quality tiers, wired like the developer's C-AiO-95:
start image -> DaSiWa_ResolutionScaleCalculator (IMAGE ASPECT, WAN/LTX Div32) -> width/height
start image -> DaSiWa_TorchResize (Target resolution, Fill and crop, Lanczos) -> first/last frame + color-match ref.
Replaces the manual width/height settings with one 'quality tier' setting.
"""
import json, sys, uuid

path, default_tier = sys.argv[1], sys.argv[2]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
assert not any(n["type"] == "DaSiWa_ResolutionScaleCalculator" for n in sg["nodes"]), "already added"

CALC, RSZ = 180, 181
names = [i["name"] for i in sg["inputs"]]
s_img, s_w, s_h = names.index("start_image"), names.index("width"), names.index("height")

# drop the manual width/height feeds and the raw-image feeds into the latent + color match
drop = [l for l in sg["links"] if l["origin_id"] == -10 and l["origin_slot"] in (s_img, s_w, s_h)
        and l["target_id"] in (98, 171)]
sg["links"] = [l for l in sg["links"] if l not in drop]
nl = max(l["id"] for l in sg["links"]) + 1
it = iter(range(nl, nl + 40))


def lk(o, os_, t, ts, typ):
    lid = next(it)
    sg["links"].append({"id": lid, "origin_id": o, "origin_slot": os_, "target_id": t, "target_slot": ts, "type": typ})
    return lid


nodes = {n["id"]: n for n in sg["nodes"]}
slot98 = {i["name"]: k for k, i in enumerate(nodes[98]["inputs"])}
img_links = [lk(-10, s_img, CALC, 0, "IMAGE"), lk(-10, s_img, RSZ, 0, "IMAGE")]
lk(CALC, 0, RSZ, 1, "INT")
lk(CALC, 1, RSZ, 2, "INT")
lk(CALC, 0, 98, slot98["width"], "INT")
lk(CALC, 1, 98, slot98["height"], "INT")
lk(RSZ, 0, 98, slot98["start_image"], "IMAGE")
lk(RSZ, 0, 98, slot98["end_image"], "IMAGE")
lk(RSZ, 0, 171, 1, "IMAGE")

calc_widgets = [default_tier, False, True, "9:16 - Social", False, 16, 9, "WAN/LTX (Div32)", 8]
calc_names = ["resolution_preset", "no_scale", "scale_from_image", "aspect_preset_when_not_image",
              "swap_aspect_when_not_image", "custom_aspect_width", "custom_aspect_height", "mode", "custom_divisor"]
rsz_widgets = ["Target resolution", "Fill and crop", 1920, 1080, 2, "Lanczos", True, 1, "0, 0, 0", "center", 0, 16, 64]
rsz_names = ["size_mode", "aspect_mode", "target_width", "target_height", "scale_multiplier", "interpolation",
             "gamma_correct", "divisible_by", "pad_color", "crop_position", "batch_size", "max_batch_megapixels", "cache_size"]
aux = {"aux_id": "darksidewalker/ComfyUI-DaSiWa-Nodes"}
sg["nodes"] += [
    {"id": CALC, "type": "DaSiWa_ResolutionScaleCalculator", "title": "Size from image + quality tier (dev: IMAGE ASPECT, Div32)",
     "pos": [1080, 640], "size": [400, 330], "flags": {}, "order": 37, "mode": 0,
     "inputs": [{"localized_name": "image", "name": "image", "shape": 7, "type": "IMAGE", "link": None},
                {"localized_name": "resolution_preset", "name": "resolution_preset", "type": "COMBO", "widget": {"name": "resolution_preset"}, "link": None}],
     "outputs": [{"localized_name": "width_int", "name": "width_int", "type": "INT", "links": None},
                 {"localized_name": "height_int", "name": "height_int", "type": "INT", "links": None},
                 {"localized_name": "width_float", "name": "width_float", "type": "FLOAT", "links": None},
                 {"localized_name": "height_float", "name": "height_float", "type": "FLOAT", "links": None}],
     "properties": {"Node name for S&R": "DaSiWa_ResolutionScaleCalculator", **aux},
     "widgets_values": calc_widgets, "widgets_values_named": dict(zip(calc_names, calc_widgets))},
    {"id": RSZ, "type": "DaSiWa_TorchResize", "title": "Resize start image to that size (dev: Fill and crop, Lanczos)",
     "pos": [1080, 1010], "size": [400, 380], "flags": {}, "order": 38, "mode": 0,
     "inputs": [{"localized_name": "image", "name": "image", "type": "IMAGE", "link": None},
                {"localized_name": "target_width", "name": "target_width", "type": "INT", "widget": {"name": "target_width"}, "link": None},
                {"localized_name": "target_height", "name": "target_height", "type": "INT", "widget": {"name": "target_height"}, "link": None}],
     "outputs": [{"localized_name": "image", "name": "image", "type": "IMAGE", "links": None}],
     "properties": {"Node name for S&R": "DaSiWa_TorchResize", **aux},
     "widgets_values": rsz_widgets, "widgets_values_named": dict(zip(rsz_names, rsz_widgets))},
]

# outside: width/height -> one quality tier setting in the same place
tier_in = {"id": str(uuid.uuid4()), "name": "resolution_preset", "type": "COMBO", "linkIds": [],
           "label": "quality tier (0.26 smoke test / 0.52 baseline, dev default / 0.65 balanced / 0.83 HD)", "pos": [0, 0]}
old = sg["inputs"]
sg["inputs"] = old[:s_w] + [tier_in] + [i for k, i in enumerate(old) if k > s_h]
tier_slot = s_w
tier_in["linkIds"].append(lk(-10, tier_slot, CALC, 1, "COMBO"))
sg["inputs"][s_img]["linkIds"] = [x for x in sg["inputs"][s_img]["linkIds"] if x not in {l["id"] for l in drop}] + img_links
lids = {l["id"] for l in sg["links"]}
for slot, i in enumerate(sg["inputs"]):
    i["linkIds"] = [x for x in i["linkIds"] if x in lids]
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["id"] in i["linkIds"]:
            l["origin_slot"] = slot

wnames = [i["name"] for i in outer["inputs"] if i.get("widget")]
vals = dict(zip(wnames, outer["widgets_values"]))
vals["resolution_preset"] = default_tier
new_outer = []
for i in outer["inputs"]:
    if i["name"] == "width":
        new_outer.append({"label": tier_in["label"], "name": "resolution_preset", "type": "COMBO",
                          "widget": {"name": "resolution_preset"}, "link": None})
    elif i["name"] != "height":
        new_outer.append(i)
outer["inputs"] = new_outer
wnames = [i["name"] for i in outer["inputs"] if i.get("widget")]
outer["widgets_values"] = [vals[n] for n in wnames]
outer["widgets_values_named"] = dict(zip(wnames, outer["widgets_values"]))

for g in sg["groups"]:
    if g["title"].startswith("3 ·"):
        g["title"] = "3 · Size (quality tier), length & FPS"
        g["bounding"][3] = max(g["bounding"][3], 1460)

for n in sg["nodes"]:
    for k, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == k]
        i["link"] = hit[0] if hit else None
    for k, o in enumerate(n.get("outputs", [])):
        hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == k]
        o["links"] = hit or None
sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], RSZ)
sg["state"]["lastLinkId"] = max(lids)

allids = {n["id"] for n in sg["nodes"]} | {-10, -20}
assert all(l["origin_id"] in allids and l["target_id"] in allids for l in sg["links"])
for slot, i in enumerate(sg["inputs"]):
    for lid in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == lid][0]["origin_slot"] == slot, i["name"]
assert len(wnames) == len(outer["widgets_values"]) == len(sg["inputs"]) - 1
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("auto size + quality tiers added to", path)
