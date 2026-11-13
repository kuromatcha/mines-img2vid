"""Exact original aspect ratio for any input image.

Before: tier size (Div32) -> resize 'Fill and crop' (trims a sliver when the ratio doesn't fit Div32).
After:  tier size (Div32) -> resize 'Fit and pad' (whole image, small white strip)
        -> generate -> decode -> crop the strip back off (exact content box) -> color match / loop / upscale / RIFE.
Content box = DaSiWa_TorchResize _fit_aspect: s = min(W/w0, H/h0); cw = max(1, round(w0*s)); ch = max(1, round(h0*s)).
Pad and crop-back both use 'center' (left = pad // 2), so the boxes line up exactly.
"""
import json, sys

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
nodes = {n["id"]: n for n in sg["nodes"]}
assert 185 not in nodes, "already added"
img_slot = [i["name"] for i in sg["inputs"]].index("start_image")

# 1) resize start image: fit + white pad instead of fill + crop
r = nodes[181]
r["widgets_values"][1] = "Fit and pad"
r["widgets_values"][8] = "255, 255, 255"
r["widgets_values_named"].update(aspect_mode="Fit and pad", pad_color="255, 255, 255")
r["title"] = "Resize start image: fit whole image + white pad (no crop)"
nodes[163]["widgets_values_named"]["expression"] = nodes[163]["widgets_values"][0]  # keep named value in sync

# 2) new nodes
GIS, CW, CH, CROP = 182, 183, 184, 185
props_core = lambda t: {"Node name for S&R": t, "cnr_id": "comfy-core"}


def math_node(nid, title, expr, pos):
    ins = [{"label": c, "localized_name": c, "name": f"values.{c}", **({} if c == "a" else {"shape": 7}),
            "type": "FLOAT,INT,BOOLEAN", "link": None} for c in "abcde"]
    ins.append({"localized_name": "expression", "name": "expression", "type": "STRING", "widget": {"name": "expression"}, "link": None})
    return {"id": nid, "type": "ComfyMathExpression", "title": title, "pos": pos, "size": [400, 200], "flags": {}, "order": 39, "mode": 0,
            "inputs": ins,
            "outputs": [{"localized_name": "FLOAT", "name": "FLOAT", "type": "FLOAT", "links": None},
                        {"localized_name": "INT", "name": "INT", "type": "INT", "links": None},
                        {"localized_name": "BOOL", "name": "BOOL", "type": "BOOLEAN", "links": None}],
            "properties": props_core("ComfyMathExpression"),
            "widgets_values": [expr], "widgets_values_named": {"expression": expr}}


rsz_names = ["size_mode", "aspect_mode", "target_width", "target_height", "scale_multiplier", "interpolation",
             "gamma_correct", "divisible_by", "pad_color", "crop_position", "batch_size", "max_batch_megapixels", "cache_size"]
crop_vals = ["Target resolution", "Fill and crop", 512, 512, 1, "Lanczos", True, 1, "255, 255, 255", "center", 0, 16, 64]
sg["nodes"] += [
    {"id": GIS, "type": "GetImageSize", "title": "Original image size", "pos": [1080, 1430], "size": [400, 120],
     "flags": {}, "order": 39, "mode": 0,
     "inputs": [{"localized_name": "image", "name": "image", "type": "IMAGE", "link": None}],
     "outputs": [{"localized_name": "width", "name": "width", "type": "INT", "links": None},
                 {"localized_name": "height", "name": "height", "type": "INT", "links": None},
                 {"localized_name": "batch_size", "name": "batch_size", "type": "INT", "links": None}],
     "properties": props_core("GetImageSize")},
    math_node(CW, "Content width inside padded frame", "max(1, round(a * min(c / a, d / b)))", [1080, 1590]),
    math_node(CH, "Content height inside padded frame", "max(1, round(b * min(c / a, d / b)))", [1080, 1830]),
    {"id": CROP, "type": "DaSiWa_TorchResize", "title": "Crop pad back off (exact original ratio)",
     "pos": [2880, 160], "size": [340, 220], "flags": {}, "order": 40, "mode": 0,
     "inputs": [{"localized_name": "image", "name": "image", "type": "IMAGE", "link": None},
                {"localized_name": "target_width", "name": "target_width", "type": "INT", "widget": {"name": "target_width"}, "link": None},
                {"localized_name": "target_height", "name": "target_height", "type": "INT", "widget": {"name": "target_height"}, "link": None}],
     "outputs": [{"localized_name": "image", "name": "image", "type": "IMAGE", "links": None}],
     "properties": {"Node name for S&R": "DaSiWa_TorchResize", "aux_id": "darksidewalker/ComfyUI-DaSiWa-Nodes"},
     "widgets_values": crop_vals, "widgets_values_named": dict(zip(rsz_names, crop_vals))},
]
nodes = {n["id"]: n for n in sg["nodes"]}

# 3) links
# decode -> crop -> color match (target); color match ref = original image (no pad)
sg["links"] = [l for l in sg["links"] if not (l["origin_id"] == 87 and l["target_id"] == 171)
               and not (l["target_id"] == 171 and l["target_slot"] == 1)]
nl = max(l["id"] for l in sg["links"]) + 1
it = iter(range(nl, nl + 40))


def lk(o, os_, t, ts, typ):
    lid = next(it)
    sg["links"].append({"id": lid, "origin_id": o, "origin_slot": os_, "target_id": t, "target_slot": ts, "type": typ})
    return lid


new_img_links = [lk(-10, img_slot, GIS, 0, "IMAGE"), lk(-10, img_slot, 171, 1, "IMAGE")]
for m in (CW, CH):
    lk(GIS, 0, m, 0, "INT")
    lk(GIS, 1, m, 1, "INT")
    lk(180, 0, m, 2, "INT")
    lk(180, 1, m, 3, "INT")
lk(87, 0, CROP, 0, "IMAGE")
lk(CW, 1, CROP, 1, "INT")
lk(CH, 1, CROP, 2, "INT")
lk(CROP, 0, 171, 0, "IMAGE")
sg["inputs"][img_slot]["linkIds"] += new_img_links

# layout: output column 1 shifts down to make room for the crop node
for nid, y in ((171, 420), (172, 660)):
    nodes[nid]["pos"] = [2880, y]
for g in sg["groups"]:
    if g["title"].startswith("3 ·"):
        g["title"] = "3 · Size (quality tier, any ratio), length & FPS"
        g["bounding"][3] = max(g["bounding"][3], 2110)
    if g["title"].startswith("7 ·"):
        g["title"] = "7 · Output (crop pad -> color match -> seamless loop -> optional upscale -> interpolation)"

lids = {l["id"] for l in sg["links"]}
for n in sg["nodes"]:
    for k, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == k]
        i["link"] = hit[0] if hit else None
    for k, o in enumerate(n.get("outputs", [])):
        hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == k]
        o["links"] = hit or None
for i in sg["inputs"]:
    i["linkIds"] = [x for x in i["linkIds"] if x in lids]
sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], CROP)
sg["state"]["lastLinkId"] = max(lids)

allids = {n["id"] for n in sg["nodes"]} | {-10, -20}
assert all(l["origin_id"] in allids and l["target_id"] in allids for l in sg["links"])
for slot, i in enumerate(sg["inputs"]):
    for lid in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == lid][0]["origin_slot"] == slot, i["name"]
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("any-ratio pad + crop-back added to", path)
