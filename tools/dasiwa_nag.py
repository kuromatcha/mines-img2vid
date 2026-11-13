"""1) Prompt: keep lips closed. 2) Developer's optional NAG (C-AiO-95: scale 11, alpha 0.25, tau 2.37, default off)
so the negative prompt works at CFG 1. Core ComfySwitchNode is lazy, so with NAG off the NAG nodes never run.
"""
import json, sys, uuid

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
assert not any(n["type"] == "NAGuidance" for n in sg["nodes"]), "already added"

# --- prompt + negative (only these two values change on the outside)
wnames = [i["name"] for i in outer["inputs"] if i.get("widget")]
vals = dict(zip(wnames, outer["widgets_values"]))
p = vals["text"]
p = p.replace("with a soft smile.", "with a soft closed-mouth smile, her lips gently pressed together.")
p = p.replace("she blinks naturally and her smile widens slightly.",
              "she blinks naturally while her lips stay closed and still, no talking.")
assert "widens" not in p and "closed-mouth" in p, "prompt text not as expected"
vals["text"] = p
vals["text_1"] = "talking, speaking, mouth moving, lip movement, open mouth, lip sync, chewing, teeth"

# --- NAG per pass, picked by a lazy switch
NH, NL, SH, SL = 176, 177, 178, 179
nl = max(l["id"] for l in sg["links"]) + 1
ids = iter(range(nl, nl + 40))


def lk(o, os_, t, ts, typ):
    lid = next(ids)
    sg["links"].append({"id": lid, "origin_id": o, "origin_slot": os_, "target_id": t, "target_slot": ts, "type": typ})
    return lid


for l in list(sg["links"]):  # shift nodes no longer feed the samplers directly
    if (l["origin_id"], l["target_id"]) in ((104, 86), (103, 85)):
        sg["links"].remove(l)

core = {"cnr_id": "comfy-core"}


def nag(nid, title, pos):
    return {"id": nid, "type": "NAGuidance", "title": title, "pos": pos, "size": [320, 150], "flags": {}, "order": 35, "mode": 0,
            "inputs": [{"localized_name": "model", "name": "model", "type": "MODEL", "link": None},
                       {"localized_name": "nag_scale", "name": "nag_scale", "type": "FLOAT", "widget": {"name": "nag_scale"}, "link": None},
                       {"localized_name": "nag_alpha", "name": "nag_alpha", "type": "FLOAT", "widget": {"name": "nag_alpha"}, "link": None},
                       {"localized_name": "nag_tau", "name": "nag_tau", "type": "FLOAT", "widget": {"name": "nag_tau"}, "link": None}],
            "outputs": [{"localized_name": "MODEL", "name": "MODEL", "type": "MODEL", "links": None}],
            "properties": {"Node name for S&R": "NAGuidance", **core},
            "widgets_values": [11, 0.25, 2.37], "widgets_values_named": {"nag_scale": 11, "nag_alpha": 0.25, "nag_tau": 2.37}}


def switch(nid, title, pos):
    return {"id": nid, "type": "ComfySwitchNode", "title": title, "pos": pos, "size": [320, 140], "flags": {}, "order": 36, "mode": 0,
            "inputs": [{"localized_name": "on_false", "name": "on_false", "shape": 7, "type": "MODEL", "link": None},
                       {"localized_name": "on_true", "name": "on_true", "shape": 7, "type": "MODEL", "link": None},
                       {"localized_name": "switch", "name": "switch", "type": "BOOLEAN", "widget": {"name": "switch"}, "link": None}],
            "outputs": [{"localized_name": "output", "name": "output", "type": "MODEL", "links": None}],
            "properties": {"Node name for S&R": "ComfySwitchNode", **core},
            "widgets_values": [False], "widgets_values_named": {"switch": False}}


sg["nodes"] += [nag(NH, "HIGH-noise NAG (dev: 11 / 0.25 / 2.37)", [2040, 200]),
                switch(SH, "HIGH: NAG on/off (off = skipped)", [2040, 380]),
                nag(NL, "LOW-noise NAG (dev: 11 / 0.25 / 2.37)", [2460, 200]),
                switch(SL, "LOW: NAG on/off (off = skipped)", [2460, 380])]
for shift, n_, sw, sampler in ((104, NH, SH, 86), (103, NL, SL, 85)):
    lk(shift, 0, n_, 0, "MODEL")
    lk(shift, 0, sw, 0, "MODEL")
    lk(n_, 0, sw, 1, "MODEL")
    lk(sw, 0, sampler, 0, "MODEL")

# outside: NAG toggle + scale, right after CFG (developer groups NAG with rendering options)
new_inputs = [
    ({"id": str(uuid.uuid4()), "name": "nag_on", "type": "BOOLEAN", "linkIds": [],
      "label": "NAG: negative prompt at CFG 1 (dev default off, uses more VRAM)", "pos": [0, 0]}, [(SH, 2), (SL, 2)], False),
    ({"id": str(uuid.uuid4()), "name": "nag_scale", "type": "FLOAT", "linkIds": [],
      "label": "NAG scale (dev: 11)", "pos": [0, 0]}, [(NH, 1), (NL, 1)], 11.0),
]
pos = [i["name"] for i in sg["inputs"]].index("cfg") + 1
for k, (inp, targets, _) in enumerate(new_inputs):
    sg["inputs"].insert(pos + k, inp)
    for t, ts in targets:
        inp["linkIds"].append(lk(-10, pos + k, t, ts, inp["type"]))
for slot, i in enumerate(sg["inputs"]):
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["id"] in i["linkIds"]:
            l["origin_slot"] = slot

wins = [i for i in outer["inputs"] if i.get("widget")]
k = [i["name"] for i in wins].index("cfg") + 1
at = outer["inputs"].index(wins[k - 1]) + 1
for j, (inp, _, val) in enumerate(new_inputs):
    outer["inputs"].insert(at + j, {"label": inp["label"], "name": inp["name"], "type": inp["type"],
                                    "widget": {"name": inp["name"]}, "link": None})
wnames = [i["name"] for i in outer["inputs"] if i.get("widget")]
vals.update({inp["name"]: val for inp, _, val in new_inputs})
outer["widgets_values"] = [vals[n] for n in wnames]
outer["widgets_values_named"] = dict(zip(wnames, outer["widgets_values"]))

# layout: samplers move down under the NAG nodes
nodes = {n["id"]: n for n in sg["nodes"]}
nodes[86]["pos"] = [2040, 560]
nodes[85]["pos"] = [2460, 560]
for g in sg["groups"]:
    if g["title"].startswith(("5 ·", "6 ·")):
        g["bounding"][3] = max(g["bounding"][3], 1180)

lids = {l["id"] for l in sg["links"]}
for n in sg["nodes"]:
    for kk, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == kk]
        i["link"] = hit[0] if hit else None
    for kk, o in enumerate(n.get("outputs", [])):
        hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == kk]
        o["links"] = hit or None
sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], SL)
sg["state"]["lastLinkId"] = max(lids)

allids = {n["id"] for n in sg["nodes"]} | {-10, -20}
assert all(l["origin_id"] in allids and l["target_id"] in allids for l in sg["links"])
for slot, i in enumerate(sg["inputs"]):
    for lid in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == lid][0]["origin_slot"] == slot, i["name"]
assert len(wnames) == len(outer["widgets_values"]) == len(sg["inputs"]) - 1
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("prompt fixed + optional NAG added to", path)
