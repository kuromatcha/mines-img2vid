"""Developer's 'Chunking' option (C-AiO-95): attention backend -> WanChunkFeedForward (KJNodes) -> shift.
Splits each block's feed-forward over the token dimension to cut peak VRAM (the 0.8 MP OOM was in the FFN).
Front toggle (default off, as in the developer's workflow) through a lazy switch, chunk count inside the subgraph.
"""
import json, sys, uuid

path, chunks = sys.argv[1], int(sys.argv[2])
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
assert not any(n["type"] == "WanChunkFeedForward" for n in sg["nodes"]), "already added"
nodes = {n["id"]: n for n in sg["nodes"]}
assert {188, 189, 103, 104} <= set(nodes), "expected attention + shift nodes"

nl = max(l["id"] for l in sg["links"]) + 1
it = iter(range(nl, nl + 40))


def lk(o, os_, t, ts, typ):
    lid = next(it)
    sg["links"].append({"id": lid, "origin_id": o, "origin_slot": os_, "target_id": t, "target_slot": ts, "type": typ})
    return lid


def chunk_node(nid, title, pos):
    return {"id": nid, "type": "WanChunkFeedForward", "title": title, "pos": pos, "size": [360, 130], "flags": {}, "order": 42, "mode": 0,
            "inputs": [{"localized_name": "model", "name": "model", "type": "MODEL", "link": None},
                       {"localized_name": "chunks", "name": "chunks", "type": "INT", "widget": {"name": "chunks"}, "link": None},
                       {"localized_name": "dim_threshold", "name": "dim_threshold", "type": "INT", "widget": {"name": "dim_threshold"}, "link": None}],
            "outputs": [{"localized_name": "model", "name": "model", "type": "MODEL", "links": None}],
            "properties": {"Node name for S&R": "WanChunkFeedForward", "cnr_id": "comfyui-kjnodes"},
            "widgets_values": [chunks, 4096], "widgets_values_named": {"chunks": chunks, "dim_threshold": 4096}}


def switch_node(nid, title, pos):
    return {"id": nid, "type": "ComfySwitchNode", "title": title, "pos": pos, "size": [360, 140], "flags": {}, "order": 43, "mode": 0,
            "inputs": [{"localized_name": "on_false", "name": "on_false", "shape": 7, "type": "MODEL", "link": None},
                       {"localized_name": "on_true", "name": "on_true", "shape": 7, "type": "MODEL", "link": None},
                       {"localized_name": "switch", "name": "switch", "type": "BOOLEAN", "widget": {"name": "switch"}, "link": None}],
            "outputs": [{"localized_name": "output", "name": "output", "type": "MODEL", "links": None}],
            "properties": {"Node name for S&R": "ComfySwitchNode", "cnr_id": "comfy-core"},
            "widgets_values": [False], "widgets_values_named": {"switch": False}}


CH, CL, SWH, SWL = 190, 191, 192, 193
sg["nodes"] += [
    chunk_node(CH, f"HIGH: FFN chunking ({chunks} chunks; more = less VRAM, slightly slower)", [0, 1170]),
    switch_node(SWH, "HIGH: chunking on/off (off = skipped)", [0, 1330]),
    chunk_node(CL, f"LOW: FFN chunking ({chunks} chunks; more = less VRAM, slightly slower)", [0, 1500]),
    switch_node(SWL, "LOW: chunking on/off (off = skipped)", [0, 1660]),
]
nodes = {n["id"]: n for n in sg["nodes"]}
toggle_links = []
for attn, shift, ch, sw in ((188, 104, CH, SWH), (189, 103, CL, SWL)):
    sg["links"] = [l for l in sg["links"] if not (l["origin_id"] == attn and l["target_id"] == shift)]
    lk(attn, 0, ch, 0, "MODEL")
    lk(attn, 0, sw, 0, "MODEL")
    lk(ch, 0, sw, 1, "MODEL")
    lk(sw, 0, shift, 0, "MODEL")

# front toggle next to the other model options (after NAG scale if present, else after CFG)
names = [i["name"] for i in sg["inputs"]]
after = "nag_scale" if "nag_scale" in names else "cfg"
pos = names.index(after) + 1
tin = {"id": str(uuid.uuid4()), "name": "chunk_on", "type": "BOOLEAN", "linkIds": [],
       "label": "FFN chunking: saves VRAM, turn on for 0.7+ MP (dev default off)", "pos": [0, 0]}
sg["inputs"].insert(pos, tin)
tin["linkIds"] += [lk(-10, pos, SWH, 2, "BOOLEAN"), lk(-10, pos, SWL, 2, "BOOLEAN")]
for slot, i in enumerate(sg["inputs"]):
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["id"] in i["linkIds"]:
            l["origin_slot"] = slot

wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
vals = dict(zip(wn, outer["widgets_values"]))
vals["chunk_on"] = False
at = [i["name"] for i in outer["inputs"]].index(after) + 1
outer["inputs"].insert(at, {"label": tin["label"], "name": "chunk_on", "type": "BOOLEAN", "widget": {"name": "chunk_on"}, "link": None})
wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
outer["widgets_values"] = [vals[n] for n in wn]
outer["widgets_values_named"] = dict(zip(wn, outer["widgets_values"]))

for g in sg["groups"]:
    if g["title"].startswith("1 ·"):
        g["title"] = "1 · Models (+ comfy kitchen attention, optional FFN chunking)"
        g["bounding"][3] = max(g["bounding"][3], 1880)

lids = {l["id"] for l in sg["links"]}
for n in sg["nodes"]:
    for k, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == k]
        i["link"] = hit[0] if hit else None
    for k, o in enumerate(n.get("outputs", [])):
        hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == k]
        o["links"] = hit or None
sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], SWL)
sg["state"]["lastLinkId"] = max(lids)
allids = {n["id"] for n in sg["nodes"]} | {-10, -20}
assert all(l["origin_id"] in allids and l["target_id"] in allids for l in sg["links"])
for slot, i in enumerate(sg["inputs"]):
    for lid in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == lid][0]["origin_slot"] == slot, i["name"]
assert len(wn) == len(outer["widgets_values"]) == len(sg["inputs"]) - 1
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("chunking added:", path.split("/")[-1])
