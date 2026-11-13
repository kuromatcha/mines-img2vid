"""Interpolation with ComfyUI's built-in nodes, skipped when off, and a clean loop point when on.

- Replaces `RIFE VFI` (ComfyUI-Frame-Interpolation, rife49.pth) with the core
  `Load Frame Interpolation Model` + `Run Frame Interpolation Model` nodes and rife_v4.26.safetensors
  (the file Seamless Loop already uses). One custom node pack and one model download less.
- Puts interpolation behind a lazy switch (multiplier > 1), so at multiplier 1 nothing is loaded or copied.
- Loop workflows: Seamless Loop now returns the first frame again at the end (exact_endpoint), the
  interpolator fills the last -> first gap like every other gap, and the duplicate frame is dropped
  afterwards. Before, the frames between the last and the first frame were missing, so an
  interpolated loop paused for one source frame at the loop point.
- Sets the fps default on the front panel to 16 (it was saved as 12; Wan 2.2 is trained at 16).
"""
import json, sys

path = sys.argv[1]
MODEL = "rife_v4.26.safetensors"
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
nodes = {n["id"]: n for n in sg["nodes"]}
assert 169 in nodes and nodes[169]["type"] == "RIFE VFI", "expected the RIFE VFI node (already converted?)"
assert {94, 170, 175} <= set(nodes), "expected create video, output fps and upscale switch"
loop = 172 in nodes and nodes[172]["type"] == "DaSiWa_SeamlessLoop"
names = [i["name"] for i in sg["inputs"]]
S_MULT, S_CKPT = names.index("multiplier"), names.index("ckpt_name")

sg["nodes"] = [n for n in sg["nodes"] if n["id"] != 169]
sg["links"] = [l for l in sg["links"] if 169 not in (l["origin_id"], l["target_id"])]
live = {l["id"] for l in sg["links"]}
for i in sg["inputs"]:
    i["linkIds"] = [x for x in i["linkIds"] if x in live]

nid = iter(range(sg["state"]["lastNodeId"] + 1, sg["state"]["lastNodeId"] + 20))
lid = iter(range(sg["state"]["lastLinkId"] + 1, sg["state"]["lastLinkId"] + 60))


def lk(o, os_, t, ts, typ):
    i = next(lid)
    sg["links"].append({"id": i, "origin_id": o, "origin_slot": os_, "target_id": t, "target_slot": ts, "type": typ})
    if o == -10:
        sg["inputs"][os_]["linkIds"].append(i)
    return i


def node(typ, title, pos, size, inputs, outputs, widgets):
    n = {"id": next(nid), "type": typ, "title": title, "pos": pos, "size": size, "flags": {}, "order": 50, "mode": 0,
         "inputs": inputs, "outputs": outputs, "properties": {"Node name for S&R": typ, "cnr_id": "comfy-core"}}
    if widgets:
        n["widgets_values"] = list(widgets.values())
        n["widgets_values_named"] = dict(widgets)
    sg["nodes"].append(n)
    return n["id"]


def pin(name, typ, widget=False, optional=False, label=None):
    p = {"localized_name": label or name, "name": name, "type": typ, "link": None}
    if label:
        p["label"] = label
    if optional:
        p["shape"] = 7
    if widget:
        p["widget"] = {"name": name}
    return p


def out(name, typ):
    return {"localized_name": name, "name": name, "type": typ, "links": None}


def math(title, pos, expr):
    num = "FLOAT,INT,BOOLEAN"
    return node("ComfyMathExpression", title, pos, [380, 180],
                [pin("values.a", num, label="a"), pin("values.b", num, optional=True, label="b"),
                 pin("expression", "STRING", widget=True)],
                [out("FLOAT", "FLOAT"), out("INT", "INT"), out("BOOL", "BOOLEAN")], {"expression": expr})


LD = node("FrameInterpolationModelLoader", "Interpolation model", [3310, 690], [380, 100],
          [pin("model_name", "COMBO", widget=True)], [out("INTERP_MODEL", "INTERP_MODEL")], {"model_name": MODEL})
MX = math("Interpolation × (at least 2)", [3310, 840], "max(a, 2)")
ON = math("Interpolation on? (× above 1)", [3310, 1070], "a > 1")
FI = node("FrameInterpolate", "Interpolate", [3720, 502], [380, 110],
          [pin("interp_model", "INTERP_MODEL"), pin("images", "IMAGE"), pin("multiplier", "INT", widget=True)],
          [out("IMAGE", "IMAGE")], {"multiplier": 2})
SW = node("ComfySwitchNode", "Interpolation on/off", [3720, 660], [380, 140],
          [pin("on_false", "IMAGE", optional=True), pin("on_true", "IMAGE", optional=True), pin("switch", "BOOLEAN", widget=True)],
          [out("output", "IMAGE")], {"switch": False})

# A front-panel setting must drive a widget inside, or ComfyUI shows it as an unconnected socket.
# The math nodes have no widget for it, so the multiplier goes through a PrimitiveInt (as steps and fps do).
PI = node("PrimitiveInt", "Interpolation multiplier", [4140, 1220], [380, 100],
          [pin("value", "INT", widget=True)], [out("INT", "INT")], {"value": 1, "control_after_generate": "fixed"})
for l in sg["links"]:                      # the existing multiplier -> output fps link
    if l["origin_id"] == -10 and l["origin_slot"] == S_MULT:
        sg["inputs"][S_MULT]["linkIds"].remove(l["id"])
        l["origin_id"], l["origin_slot"] = PI, 0
lk(-10, S_MULT, PI, 0, "INT")
lk(-10, S_CKPT, LD, 0, "COMBO")
lk(PI, 0, MX, 0, "INT")
lk(PI, 0, ON, 0, "INT")
lk(LD, 0, FI, 0, "INTERP_MODEL")
lk(175, 0, FI, 1, "IMAGE")
lk(MX, 1, FI, 2, "INT")
lk(175, 0, SW, 0, "IMAGE")
lk(FI, 0, SW, 1, "IMAGE")
lk(ON, 2, SW, 2, "BOOLEAN")

last = SW
if loop:
    sl = nodes[172]
    sl["widgets_values_named"]["exact_endpoint"] = True
    sl["widgets_values"] = list(sl["widgets_values_named"].values())
    SZ = node("GetImageSize", "Frame count (with repeated first frame)", [3310, 1300], [380, 120],
              [pin("image", "IMAGE")], [out("width", "INT"), out("height", "INT"), out("batch_size", "INT")], None)
    M1 = math("Frame count − 1", [3310, 1470], "max(a - 1, 1)")
    TR = node("ImageFromBatch", "Drop repeated first frame", [3720, 850], [380, 130],
              [pin("image", "IMAGE"), pin("batch_index", "INT", widget=True), pin("length", "INT", widget=True)],
              [out("IMAGE", "IMAGE")], {"batch_index": 0, "length": 4096})
    lk(SW, 0, SZ, 0, "IMAGE")
    lk(SZ, 2, M1, 0, "INT")
    lk(SW, 0, TR, 0, "IMAGE")
    lk(M1, 1, TR, 2, "INT")
    last = TR
lk(last, 0, 94, 0, "IMAGE")
nodes[94]["pos"] = [3720, 1030]

for g in sg["groups"]:
    g["bounding"][3] = max(g["bounding"][3], 1760)

# front panel: interpolation model file and fps default
wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
vals = dict(zip(wn, outer["widgets_values"]))
vals["ckpt_name"] = MODEL
vals["value_4"] = 16.0
outer["widgets_values"] = [vals[n] for n in wn]
outer["widgets_values_named"] = dict(vals)

# rebuild link bookkeeping and check the wiring
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
assert nodes[94]["inputs"][0]["link"] is not None
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("core interpolation" + (" + loop wrap" if loop else "") + ":", path.replace("\\", "/").split("/")[-1])
