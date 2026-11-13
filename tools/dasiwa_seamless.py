"""Developer loop chain (DaSiWa C-AiO-95 post-processing): decode -> color match -> Seamless Loop -> interpolation -> video.

Seamless Loop picks the seam, trims bad end frames and morphs tail into head with RIFE 4.26,
so the old 'drop duplicate last frame' trim (nodes 167/168) is removed.
"""
import json, sys

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
assert not any(n["type"] == "DaSiWa_SeamlessLoop" for n in sg["nodes"]), "already added"

REMOVE = {167, 168}
sg["nodes"] = [n for n in sg["nodes"] if n["id"] not in REMOVE]
sg["links"] = [l for l in sg["links"] if l["origin_id"] not in REMOVE and l["target_id"] not in REMOVE]
nodes = {n["id"]: n for n in sg["nodes"]}

SL = 172
nl = max(l["id"] for l in sg["links"]) + 1
for l in list(sg["links"]):  # color match no longer feeds RIFE directly
    if l["origin_id"] == 171 and l["target_id"] == 169:
        sg["links"].remove(l)
sg["links"] += [
    {"id": nl, "origin_id": 171, "origin_slot": 0, "target_id": SL, "target_slot": 0, "type": "IMAGE"},
    {"id": nl + 1, "origin_id": SL, "origin_slot": 0, "target_id": 169, "target_slot": 0, "type": "IMAGE"},
    {"id": nl + 2, "origin_id": 169, "origin_slot": 0, "target_id": 94, "target_slot": 0, "type": "IMAGE"},
]
sg["nodes"].append({
    "id": SL, "type": "DaSiWa_SeamlessLoop", "title": "Seamless Loop (dev: RIFE 4.26, exact_endpoint off)",
    "pos": [2880, 400], "size": [340, 220], "flags": {}, "order": 31, "mode": 0,
    "inputs": [
        {"localized_name": "images", "name": "images", "type": "IMAGE", "link": nl},
        {"localized_name": "model_name", "name": "model_name", "shape": 7, "type": "COMBO", "widget": {"name": "model_name"}, "link": None},
        {"localized_name": "audio", "name": "audio", "shape": 7, "type": "AUDIO", "link": None},
    ],
    "outputs": [
        {"localized_name": "images", "name": "images", "type": "IMAGE", "links": [nl + 1]},
        {"localized_name": "audio", "name": "audio", "type": "AUDIO", "links": None},
    ],
    "properties": {"Node name for S&R": "DaSiWa_SeamlessLoop", "aux_id": "darksidewalker/ComfyUI-DaSiWa-Nodes"},
    "widgets_values": ["rife_v4.26.safetensors", False, "RIFE / FILM", "HIGH", 0, 0.0, "Crossfade"],
    "widgets_values_named": {"model_name": "rife_v4.26.safetensors", "exact_endpoint": False,
                             "interpolation_backend": "RIFE / FILM", "rtx_mode": "HIGH", "rtx_device_id": 0,
                             "frame_rate": 0.0, "audio_loop": "Crossfade"},
})
nodes = {n["id"]: n for n in sg["nodes"]}
nodes[169]["title"] = "Interpolation (multiplier set outside, 1 = off)"
for nid, y in ((169, 660), (94, 1060)):
    nodes[nid]["pos"] = [2880, y]
for g in sg["groups"]:
    if g["title"].startswith("7 ·"):
        g["title"] = "7 · Output (color match -> seamless loop -> interpolation)"
        g["bounding"][3] = max(g["bounding"][3], 1340)

# rebuild link fields everywhere from the link table
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
sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], SL)
sg["state"]["lastLinkId"] = nl + 2

ids = {n["id"] for n in sg["nodes"]} | {-10, -20}
assert all(l["origin_id"] in ids and l["target_id"] in ids for l in sg["links"])
for slot, i in enumerate(sg["inputs"]):
    for lid in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == lid][0]["origin_slot"] == slot
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("added seamless loop to", path)
