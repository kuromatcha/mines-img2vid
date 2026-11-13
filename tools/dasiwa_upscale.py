"""Optional model upscale, in the developer's position (C-AiO-95): seamless loop -> upscale with model -> interpolation.

Uses core nodes only. ComfySwitchNode inputs are lazy, so with the toggle off the upscaler never loads or runs.
"""
import json, sys, uuid

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
assert not any(n["type"] == "ImageUpscaleWithModel" for n in sg["nodes"]), "already added"

LOADER, UPS, SW = 173, 174, 175
MODEL = "2x-AnimeSharpV4_RCAN.safetensors"
nl = max(l["id"] for l in sg["links"]) + 1
L = dict(loop_to_ups=nl, model=nl + 1, loop_to_sw=nl + 2, ups_to_sw=nl + 3, sw_to_rife=nl + 4, in_on=nl + 5, in_model=nl + 6)

for l in list(sg["links"]):  # seamless loop no longer feeds interpolation directly
    if l["origin_id"] == 172 and l["target_id"] == 169:
        sg["links"].remove(l)


def lk(lid, o, os_, t, ts, typ):
    sg["links"].append({"id": lid, "origin_id": o, "origin_slot": os_, "target_id": t, "target_slot": ts, "type": typ})


lk(L["loop_to_ups"], 172, 0, UPS, 1, "IMAGE")
lk(L["model"], LOADER, 0, UPS, 0, "UPSCALE_MODEL")
lk(L["loop_to_sw"], 172, 0, SW, 0, "IMAGE")
lk(L["ups_to_sw"], UPS, 0, SW, 1, "IMAGE")
lk(L["sw_to_rife"], SW, 0, 169, 0, "IMAGE")

core = {"cnr_id": "comfy-core"}
sg["nodes"] += [
    {"id": LOADER, "type": "UpscaleModelLoader", "title": "Upscale model (dev: 2x-AnimeSharpV4_RCAN)",
     "pos": [3300, 30], "size": [360, 100], "flags": {}, "order": 32, "mode": 0,
     "inputs": [{"localized_name": "model_name", "name": "model_name", "type": "COMBO", "widget": {"name": "model_name"}, "link": None}],
     "outputs": [{"localized_name": "UPSCALE_MODEL", "name": "UPSCALE_MODEL", "type": "UPSCALE_MODEL", "links": None}],
     "properties": {"Node name for S&R": "UpscaleModelLoader", **core},
     "widgets_values": [MODEL], "widgets_values_named": {"model_name": MODEL}},
    {"id": UPS, "type": "ImageUpscaleWithModel", "title": "Upscale frames with model (slow, more VRAM)",
     "pos": [3300, 190], "size": [360, 100], "flags": {}, "order": 33, "mode": 0,
     "inputs": [{"localized_name": "upscale_model", "name": "upscale_model", "type": "UPSCALE_MODEL", "link": None},
                {"localized_name": "image", "name": "image", "type": "IMAGE", "link": None}],
     "outputs": [{"localized_name": "IMAGE", "name": "IMAGE", "type": "IMAGE", "links": None}],
     "properties": {"Node name for S&R": "ImageUpscaleWithModel", **core}},
    {"id": SW, "type": "ComfySwitchNode", "title": "Upscale on/off (off = skipped entirely)",
     "pos": [3300, 360], "size": [360, 140], "flags": {}, "order": 34, "mode": 0,
     "inputs": [{"localized_name": "on_false", "name": "on_false", "shape": 7, "type": "IMAGE", "link": None},
                {"localized_name": "on_true", "name": "on_true", "shape": 7, "type": "IMAGE", "link": None},
                {"localized_name": "switch", "name": "switch", "type": "BOOLEAN", "widget": {"name": "switch"}, "link": None}],
     "outputs": [{"localized_name": "output", "name": "output", "type": "IMAGE", "links": None}],
     "properties": {"Node name for S&R": "ComfySwitchNode", **core},
     "widgets_values": [False], "widgets_values_named": {"switch": False}},
]

# outside settings after color match strength, before interpolation (developer order)
new_inputs = [
    ({"id": str(uuid.uuid4()), "name": "switch", "type": "BOOLEAN", "linkIds": [L["in_on"]],
      "label": "upscale with model (dev default off)", "pos": [0, 0]}, SW, 2, False),
    ({"id": str(uuid.uuid4()), "name": "model_name", "type": "COMBO", "linkIds": [L["in_model"]],
      "label": "upscale model", "pos": [0, 0]}, LOADER, 0, MODEL),
]
pos = [i["name"] for i in sg["inputs"]].index("multiplier")
for k, (inp, tgt, tslot, _) in enumerate(new_inputs):
    sg["inputs"].insert(pos + k, inp)
    lk(inp["linkIds"][0], -10, pos + k, tgt, tslot, inp["type"])
for slot, i in enumerate(sg["inputs"]):
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["id"] in i["linkIds"]:
            l["origin_slot"] = slot

wins = [i for i in outer["inputs"] if i.get("widget")]
k = [i["name"] for i in wins].index("multiplier")
at = outer["inputs"].index(wins[k])
for j, (inp, _, _, val) in enumerate(new_inputs):
    outer["inputs"].insert(at + j, {"label": inp["label"], "name": inp["name"], "type": inp["type"],
                                    "widget": {"name": inp["name"]}, "link": None})
    outer["widgets_values"].insert(k + j, val)
outer["widgets_values_named"] = {i["name"]: v for i, v in zip([i for i in outer["inputs"] if i.get("widget")], outer["widgets_values"])}

# layout: second column in the Output group
nodes = {n["id"]: n for n in sg["nodes"]}
nodes[169]["pos"] = [3300, 560]
nodes[94]["pos"] = [3300, 960]
for g in sg["groups"]:
    if g["title"].startswith("7 ·"):
        g["title"] = "7 · Output (color match -> seamless loop -> optional upscale -> interpolation)"
        g["bounding"] = [2860, g["bounding"][1], 820, max(g["bounding"][3], 1340)]

# rebuild link fields from the link table
lids = {l["id"] for l in sg["links"]}
for n in sg["nodes"]:
    for kk, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == kk]
        i["link"] = hit[0] if hit else None
    for kk, o in enumerate(n.get("outputs", [])):
        hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == kk]
        o["links"] = hit or None
sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], SW)
sg["state"]["lastLinkId"] = max(lids)

ids = {n["id"] for n in sg["nodes"]} | {-10, -20}
assert all(l["origin_id"] in ids and l["target_id"] in ids for l in sg["links"])
for slot, i in enumerate(sg["inputs"]):
    for lid in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == lid][0]["origin_slot"] == slot, i["name"]
assert len([i for i in outer["inputs"] if i.get("widget")]) == len(outer["widgets_values"]) == len(sg["inputs"]) - 1
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("added optional upscale to", path)
