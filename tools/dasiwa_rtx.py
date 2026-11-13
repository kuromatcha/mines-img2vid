"""Optional RTX Video Super Resolution upscale (RTX Upscaler & Refiner from ComfyUI-DaSiWa-Nodes, needs `nvidia-vfx`).

Front toggle (default off) through a lazy switch placed after the model-upscale switch:
off = the existing path (AnimeSharp upscale or none), on = RTX VSR 2x on the frames *before* the model upscale,
so the two never stack and the unused one is not executed. Quality/mode/scale stay inside the subgraph.
Run after dasiwa_coreinterp.py.
"""
import json, sys, uuid

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
nodes = {n["id"]: n for n in sg["nodes"]}
assert not any(n["type"] == "DaSiWa_RTX_UpscalerRefiner" for n in sg["nodes"]), "already added"
assert {174, 175} <= set(nodes) and nodes[175]["type"] == "ComfySwitchNode", "expected model upscale + its switch"
assert any(n["type"] == "FrameInterpolate" for n in sg["nodes"]), "run dasiwa_coreinterp.py first"

link = {l["id"]: l for l in sg["links"]}
src = link[nodes[174]["inputs"][1]["link"]]           # frames going into the model upscale
src_node, src_slot = src["origin_id"], src["origin_slot"]
consumers = [l for l in sg["links"] if l["origin_id"] == 175]
assert consumers, "upscale switch has no consumers"

nid = iter(range(sg["state"]["lastNodeId"] + 1, sg["state"]["lastNodeId"] + 10))
lid = iter(range(sg["state"]["lastLinkId"] + 1, sg["state"]["lastLinkId"] + 30))


def lk(o, os_, t, ts, typ):
    i = next(lid)
    sg["links"].append({"id": i, "origin_id": o, "origin_slot": os_, "target_id": t, "target_slot": ts, "type": typ})
    return i


Q = ["Low", "Medium", "High", "Ultra"]
W = [  # (name, type, value, optional) in the node's own order
    ("denoise", "BOOLEAN", False, 0), ("denoise_quality", "COMBO", "Ultra", 0),
    ("deblur", "BOOLEAN", False, 0), ("deblur_quality", "COMBO", "Ultra", 0),
    ("upscale", "COMBO", "VSR", 0), ("upscale_quality", "COMBO", "Ultra", 0),
    ("resize_type", "COMBO", "Scale", 0), ("scale", "FLOAT", 2.0, 0), ("megapixels", "FLOAT", 2.0, 0),
    ("width", "INT", 1920, 0), ("height", "INT", 1080, 0), ("divisible_by", "COMBO", "8", 0),
    ("ratio_preset", "COMBO", "16:9", 0), ("resize_method", "COMBO", "Center Crop (Fill)", 0), ("device_id", "INT", 0, 0),
    ("empty_cache", "BOOLEAN", False, 1), ("use_mmap", "BOOLEAN", False, 1), ("auto_unload_models", "BOOLEAN", True, 1),
    ("chunking", "BOOLEAN", True, 1), ("lossless_fp16", "BOOLEAN", True, 1), ("chunk_frames", "INT", 16, 1),
    ("image_encoding", "COMBO", "8-bit RGB", 1), ("denoise_strength", "FLOAT", 1.0, 1),
    ("deblur_strength", "FLOAT", 1.0, 1), ("upscale_strength", "FLOAT", 1.0, 1), ("preserve_alpha", "BOOLEAN", False, 1),
    ("channel_integrity_check", "BOOLEAN", False, 1), ("hdr_enabled", "BOOLEAN", False, 1), ("hdr_contrast", "INT", 100, 1),
    ("hdr_saturation", "INT", 100, 1), ("hdr_middle_gray", "INT", 50, 1), ("hdr_luminance", "INT", 650, 1),
    ("hdr_debanding", "BOOLEAN", True, 1),
]


def wpin(name, typ, optional):
    p = {"localized_name": name, "name": name, "type": typ, "widget": {"name": name}, "link": None}
    if optional:
        p["shape"] = 7
    return p


RTX, SW = next(nid), next(nid)
vals = {n: v for n, _, v, _ in W}
sg["nodes"].append({
    "id": RTX, "type": "DaSiWa_RTX_UpscalerRefiner", "title": "RTX upscale (VSR 2×)", "pos": [4140, 0], "size": [400, 980],
    "flags": {}, "order": 51, "mode": 0,
    "inputs": [{"localized_name": "images", "name": "images", "type": "IMAGE", "link": None}] + [wpin(n, t, o) for n, t, _, o in W],
    "outputs": [{"localized_name": "images", "name": "images", "type": "IMAGE", "links": None}],
    "properties": {"Node name for S&R": "DaSiWa_RTX_UpscalerRefiner", "aux_id": "darksidewalker/ComfyUI-DaSiWa-Nodes"},
    "widgets_values": list(vals.values()), "widgets_values_named": dict(vals)})
sg["nodes"].append({
    "id": SW, "type": "ComfySwitchNode", "title": "RTX upscale on/off", "pos": [4140, 1030], "size": [400, 140],
    "flags": {}, "order": 52, "mode": 0,
    "inputs": [{"localized_name": "on_false", "name": "on_false", "shape": 7, "type": "IMAGE", "link": None},
               {"localized_name": "on_true", "name": "on_true", "shape": 7, "type": "IMAGE", "link": None},
               {"localized_name": "switch", "name": "switch", "type": "BOOLEAN", "widget": {"name": "switch"}, "link": None}],
    "outputs": [{"localized_name": "output", "name": "output", "type": "IMAGE", "links": None}],
    "properties": {"Node name for S&R": "ComfySwitchNode", "cnr_id": "comfy-core"},
    "widgets_values": [False], "widgets_values_named": {"switch": False}})

for l in consumers:                                   # everything after the model-upscale switch now reads the RTX switch
    l["origin_id"] = SW
lk(src_node, src_slot, RTX, 0, "IMAGE")
lk(175, 0, SW, 0, "IMAGE")
lk(RTX, 0, SW, 1, "IMAGE")

# front toggle right after the upscale model picker
names = [i["name"] for i in sg["inputs"]]
pos = names.index("model_name") + 1
label = "RTX upscale 2× (fast, used instead of the upscale model)"
tin = {"id": str(uuid.uuid4()), "name": "rtx_on", "type": "BOOLEAN", "linkIds": [], "label": label, "pos": [0, 0]}
sg["inputs"].insert(pos, tin)
tin["linkIds"].append(lk(-10, pos, SW, 2, "BOOLEAN"))
for slot, i in enumerate(sg["inputs"]):
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["id"] in i["linkIds"]:
            l["origin_slot"] = slot

wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
ov = dict(zip(wn, outer["widgets_values"]))
ov["rtx_on"] = False
at = [i["name"] for i in outer["inputs"]].index("model_name") + 1
outer["inputs"].insert(at, {"label": label, "name": "rtx_on", "type": "BOOLEAN", "widget": {"name": "rtx_on"}, "link": None})
wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
outer["widgets_values"] = [ov[n] for n in wn]
outer["widgets_values_named"] = dict(zip(wn, outer["widgets_values"]))

for g in sg["groups"]:
    if g["title"].startswith("7"):
        g["bounding"][2] = max(g["bounding"][2], 1270)

for n in sg["nodes"]:
    for k, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == k]
        assert len(hit) <= 1, (n["id"], i["name"])
        i["link"] = hit[0] if hit else None
    for k, o in enumerate(n.get("outputs", [])):
        hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == k]
        o["links"] = hit or None
sg["state"]["lastNodeId"] = max(n["id"] for n in sg["nodes"])
sg["state"]["lastLinkId"] = max(l["id"] for l in sg["links"])
ids = {n["id"] for n in sg["nodes"]} | {-10, -20}
assert all(l["origin_id"] in ids and l["target_id"] in ids for l in sg["links"])
for slot, i in enumerate(sg["inputs"]):
    assert i["linkIds"], i["name"]
    for x in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == x][0]["origin_slot"] == slot, i["name"]
assert len(wn) == len(outer["widgets_values"]) == len(sg["inputs"]) - 1
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("RTX upscale added:", path.replace("\\", "/").split("/")[-1])
