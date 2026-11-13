"""Add the developer's color match (core ColorTransfer, reinhard_lab, per_frame, 0.75) to the DaSiWa loop.

Developer wiring (C-AiO-95): decoded frames -> ColorTransfer(image_ref = first-frame image) -> loop/interpolation.
"""
import json, sys, uuid

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
nodes = {n["id"]: n for n in sg["nodes"]}
assert not any(n["type"] == "ColorTransfer" for n in sg["nodes"]), "already added"

CT = 171
nl = max(l["id"] for l in sg["links"]) + 1
l_target, l_ref, l_out, l_str = nl, nl + 1, nl + 2, nl + 3

# decoded frames now go to color match, color match feeds RIFE
for l in sg["links"]:
    if l["origin_id"] == 87 and l["target_id"] == 169:
        sg["links"].remove(l)
        break
sg["links"] += [
    {"id": l_target, "origin_id": 87, "origin_slot": 0, "target_id": CT, "target_slot": 0, "type": "IMAGE"},
    {"id": l_ref, "origin_id": -10, "origin_slot": 0, "target_id": CT, "target_slot": 1, "type": "IMAGE"},
    {"id": l_out, "origin_id": CT, "origin_slot": 0, "target_id": 169, "target_slot": 0, "type": "IMAGE"},
]
sg["nodes"].append({
    "id": CT, "type": "ColorTransfer", "title": "Color match to start image (dev: reinhard_lab, per_frame, 0.75)",
    "pos": [2880, 160], "size": [340, 200], "flags": {}, "order": 30, "mode": 0,
    "inputs": [
        {"localized_name": "image_target", "name": "image_target", "type": "IMAGE", "link": l_target},
        {"localized_name": "image_ref", "name": "image_ref", "type": "IMAGE", "link": l_ref},
        {"localized_name": "strength", "name": "strength", "type": "FLOAT", "widget": {"name": "strength"}, "link": None},
    ],
    "outputs": [{"localized_name": "image", "name": "image", "type": "IMAGE", "links": [l_out]}],
    "properties": {"Node name for S&R": "ColorTransfer", "cnr_id": "comfy-core"},
    "widgets_values": ["reinhard_lab", "per_frame", 0.75],
    "widgets_values_named": {"method": "reinhard_lab", "source_stats": "per_frame", "strength": 0.75},
})
nodes = {n["id"]: n for n in sg["nodes"]}
nodes[87]["outputs"][0]["links"] = [l_target]
nodes[169]["inputs"][0]["link"] = l_out
sg["inputs"][0]["linkIds"].append(l_ref)

# expose strength outside, right before the interpolation settings
str_in = {"id": str(uuid.uuid4()), "name": "strength", "type": "FLOAT", "linkIds": [l_str],
          "label": "color match strength (dev: 0.75, 0 = off)", "pos": [0, 0]}
pos = [i["name"] for i in sg["inputs"]].index("multiplier")
sg["inputs"].insert(pos, str_in)
sg["links"].append({"id": l_str, "origin_id": -10, "origin_slot": pos, "target_id": CT, "target_slot": 2, "type": "FLOAT"})
nodes[CT]["inputs"][2]["link"] = l_str
for slot, i in enumerate(sg["inputs"]):  # re-point slots after the insert
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["id"] in i["linkIds"]:
            l["origin_slot"] = slot

# make room in the Output group
for nid, y in ((169, 400), (168, 800), (94, 990)):
    nodes[nid]["pos"] = [2880, y]
for g in sg["groups"]:
    if g["title"].startswith("7 ·"):
        g["title"] = "7 · Output (color match, interpolation, loop trim)"
        g["bounding"][3] = max(g["bounding"][3], 1260)
sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], CT)
sg["state"]["lastLinkId"] = l_str

# outside widget, same position as the subgraph input
wins = [i for i in outer["inputs"] if i.get("widget")]
k = [i["name"] for i in wins].index("multiplier")
outer["inputs"].insert(outer["inputs"].index(wins[k]), {"label": str_in["label"], "name": "strength", "type": "FLOAT",
                                                        "widget": {"name": "strength"}, "link": None})
outer["widgets_values"].insert(k, 0.75)
named = outer.setdefault("widgets_values_named", {})
outer["widgets_values_named"] = {i["name"]: v for i, v in zip([i for i in outer["inputs"] if i.get("widget")], outer["widgets_values"])}

# checks
ids = {n["id"] for n in sg["nodes"]} | {-10, -20}
lids = {l["id"] for l in sg["links"]}
assert all(l["origin_id"] in ids and l["target_id"] in ids for l in sg["links"])
for n in sg["nodes"]:
    for i in n["inputs"]:
        assert i["link"] is None or i["link"] in lids, (n["id"], i["name"])
for slot, i in enumerate(sg["inputs"]):
    for lid in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == lid][0]["origin_slot"] == slot, i["name"]
assert len([i for i in outer["inputs"] if i.get("widget")]) == len(outer["widgets_values"]) == len(sg["inputs"]) - 1
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("added color match to", path)
