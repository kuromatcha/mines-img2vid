"""Rewire the DaSiWa loop workflow to the developer's (DaSiWa C-AiO-95, FLF2V engine) defaults.

Developer default chain: UNet (High/Low) -> ModelSamplingSD3 shift 5 -> KSamplerAdvanced
(4 steps total, split 2, CFG 1, euler/simple). No speed-up LoRAs, NAG off, interpolation off.
Frame count: (round(sec*fps/8)*8)+1. Keeps the clean layout (titled nodes, groups, settings outside).
"""
import json, sys, uuid

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
nodes = {n["id"]: n for n in sg["nodes"]}

# values currently set on the outside, by input name
old_names = [i["name"] for i in outer["inputs"] if i.get("widget")]
vals = dict(zip(old_names, outer["widgets_values"]))

REMOVE = {101, 102, 116, 117, 119, 120, 125, 131, 126, 127, 128, 165, 166}
sg["nodes"] = [n for n in sg["nodes"] if n["id"] not in REMOVE]
nodes = {n["id"]: n for n in sg["nodes"]}
sg["links"] = [l for l in sg["links"] if l["origin_id"] not in REMOVE and l["target_id"] not in REMOVE]

next_link = [max(l["id"] for l in sg["links"]) + 1]


def link(o, oslot, t, tname, typ):
    tnode = nodes[t]
    tslot = [i["name"] for i in tnode["inputs"]].index(tname)
    for l in list(sg["links"]):  # drop whatever fed this input before
        if l["target_id"] == t and l["target_slot"] == tslot:
            sg["links"].remove(l)
    lid = next_link[0]
    next_link[0] += 1
    sg["links"].append({"id": lid, "origin_id": o, "origin_slot": oslot, "target_id": t, "target_slot": tslot, "type": typ})
    return lid


def unlink(t, tname, widget_value=None, widget_index=None):
    tnode = nodes[t]
    tslot = [i["name"] for i in tnode["inputs"]].index(tname)
    sg["links"] = [l for l in sg["links"] if not (l["target_id"] == t and l["target_slot"] == tslot)]
    if widget_index is not None:
        tnode["widgets_values"][widget_index] = widget_value
        if "widgets_values_named" in tnode:
            tnode["widgets_values_named"][tname] = widget_value


# model chain: UNet -> shift -> sampler (no LoRA, no switch, no NAG)
link(95, 0, 104, "model", "MODEL")
link(96, 0, 103, "model", "MODEL")
link(104, 0, 86, "model", "MODEL")
link(103, 0, 85, "model", "MODEL")
# steps / split / cfg primitives feed both samplers directly
for s in (86, 85):
    link(118, 0, s, "steps", "INT")
    link(122, 0, s, "cfg", "FLOAT")
link(124, 0, 86, "end_at_step", "INT")
link(124, 0, 85, "start_at_step", "INT")
unlink(85, "end_at_step", 10000, 8)  # developer: low pass runs to the end

# subgraph inputs: drop LoRA strength, NAG, turbo; add CFG; new outside order
keep = {i["name"]: i for i in sg["inputs"]}
cfg_in = {"id": str(uuid.uuid4()), "name": "cfg", "type": "FLOAT", "linkIds": [], "label": "CFG (1 = ignore negative; dev range 1-1.5)", "pos": [0, 0]}
labels = {
    "value_2": "steps total (dev: 4)",
    "value_3": "high/low split step (dev: 2)",
    "shift": "shift high + low (dev: 5, valid 5-10)",
    "value_1": "duration (seconds)",
    "value_4": "fps (dev: 16)",
    "multiplier": "interpolation multiplier (1 = off, dev default off)",
}
order = ["start_image", "text", "text_1", "width", "height", "value_1", "value_4", "noise_seed",
         "value_2", "value_3", "cfg", "shift", "sampler_name", "scheduler", "multiplier", "ckpt_name"]
new_inputs = []
for name in order:
    i = cfg_in if name == "cfg" else keep[name]
    if name in labels:
        i["label"] = labels[name]
    new_inputs.append(i)
sg["inputs"] = new_inputs

# re-point every subgraph-input link to its new slot; add cfg / steps / split feeds
by_old = {}
for i in new_inputs:
    for lid in i["linkIds"]:
        by_old[lid] = i
sg["links"] = [l for l in sg["links"] if l["origin_id"] != -10 or l["id"] in by_old]
for slot, i in enumerate(new_inputs):
    i["linkIds"] = [l for l in i["linkIds"] if any(x["id"] == l for x in sg["links"])]
    for l in sg["links"]:
        if l["id"] in i["linkIds"]:
            l["origin_slot"] = slot
cfg_slot = order.index("cfg")
cfg_in["linkIds"] = [link(-10, cfg_slot, 122, "value", "FLOAT")]

# rebuild every node's input/output link fields from the link table
lids = {l["id"]: l for l in sg["links"]}
for n in sg["nodes"]:
    for k, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == k]
        i["link"] = hit[0] if hit else None
    for k, o in enumerate(n.get("outputs", [])):
        hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == k]
        o["links"] = hit or None
for o in sg["outputs"]:
    o["linkIds"] = [l for l in o["linkIds"] if l in lids]

# titles, values, layout
T = {
    95: ("HIGH-noise model - DaSiWa v11 (sets motion)", [0, 30]),
    96: ("LOW-noise model - DaSiWa v11 (adds detail)", [0, 230]),
    84: (None, [0, 430]), 90: (None, [0, 660]),
    118: ("Steps total (dev: 4)", [1580, 30]),
    124: ("High/low split step (dev: 2)", [1580, 220]),
    122: ("CFG (dev: 1)", [1580, 410]),
    104: ("HIGH-noise shift", [2040, 30]), 86: ("HIGH-noise sampler (steps 0 -> split)", [2040, 220]),
    103: ("LOW-noise shift", [2460, 30]), 85: ("LOW-noise sampler (split -> end)", [2460, 220]),
    87: (None, [2880, 30]), 169: (None, [2880, 200]), 168: (None, [2880, 600]), 94: (None, [2880, 790]),
    163: ("Frame count (dev: round(sec x fps / 8) x 8 + 1)", None),
}
for nid, (title, pos) in T.items():
    if title:
        nodes[nid]["title"] = title
    if pos:
        nodes[nid]["pos"] = pos
nodes[163]["widgets_values"][0] = "(round((a * b) / 8) * 8) +1"
for g in sg["groups"]:
    t = g["title"]
    if t.startswith("5 ·"):
        g["title"] = None
    elif t.startswith("4 ·"):
        g["title"], g["bounding"][2] = "4 · Sampling settings (developer defaults)", 400
    elif t.startswith("6 ·"):
        g["title"], g["bounding"][0] = "5 · HIGH-noise pass (motion)", 2020
    elif t.startswith("7 ·"):
        g["title"], g["bounding"][0] = "6 · LOW-noise pass (detail)", 2440
    elif t.startswith("8 ·"):
        g["title"], g["bounding"][0] = "7 · Output", 2860
sg["groups"] = [g for g in sg["groups"] if g["title"]]
sg["state"]["lastLinkId"] = next_link[0] - 1

# outer node: same order as subgraph inputs, developer values
vals.update({"value_2": 4, "value_3": 2, "cfg": 1.0, "shift": 5.0, "sampler_name": "euler", "scheduler": "simple",
             "value_4": 16, "multiplier": 1})
image_in = outer["inputs"][0]
by_name = {i["name"]: i for i in outer["inputs"]}
wins, wvals = [], []
for i in new_inputs[1:]:
    oi = by_name.get(i["name"], {"name": i["name"], "type": i["type"], "widget": {"name": i["name"]}, "link": None})
    oi["label"] = i.get("label", oi.get("label"))
    if oi.get("label") is None:
        oi.pop("label", None)
    wins.append(oi)
    wvals.append(vals[i["name"]])
outer["inputs"] = [image_in] + wins
outer["widgets_values"] = wvals
outer["widgets_values_named"] = {i["name"]: v for i, v in zip(wins, wvals)}

# checks
ids = {n["id"] for n in sg["nodes"]} | {-10, -20}
lids = {l["id"] for l in sg["links"]}
assert all(l["origin_id"] in ids and l["target_id"] in ids for l in sg["links"])
for n in sg["nodes"]:
    for i in n["inputs"]:
        assert i["link"] is None or i["link"] in lids
for k, i in enumerate(sg["inputs"]):
    for lid in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == lid][0]["origin_slot"] == k
assert not any(n["type"] in ("LoraLoaderModelOnly", "NAGuidance", "ComfySwitchNode") for n in sg["nodes"])
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("rewired", path)
