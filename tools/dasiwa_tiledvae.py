"""Optional tiled VAE decode (the developer's C-AiO-95 has a 'Tiled VAE' switch).

Usage: python -I tools/dasiwa_tiledvae.py <workflow> [<workflow> ...]   (I2V and Loop workflows)

Decoding all frames in one pass is the last VRAM peak of a run. The core 'VAE Decode (Tiled)' node decodes in
overlapping tiles and frame windows instead: lower peak, a little slower. A front-panel toggle 'tiled VAE decode'
(default off, after FFN chunking) picks between the two decoders through a lazy switch, so only one runs.
Run dasiwa_layout.py afterwards to place the new nodes.
"""
import json, sys, uuid

TILED, SWITCH, AFTER = "Decode latent to frames (tiled)", "Switch: tiled VAE decode", "chunk_on"

for path in sys.argv[1:]:
    d = json.load(open(path, encoding="utf-8"))
    sg = d["definitions"]["subgraphs"][0]
    outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
    T = {n.get("title"): n for n in sg["nodes"]}
    assert TILED not in T, "already added"
    dec = T["Decode latent to frames"]
    assert dec["type"] == "VAEDecode"
    src = {l["target_slot"]: l for l in sg["links"] if l["target_id"] == dec["id"]}  # 0 samples, 1 vae

    nid = max(n["id"] for n in sg["nodes"])
    tid, sid = nid + 1, nid + 2
    lid = [max(l["id"] for l in sg["links"])]

    def lk(o, os_, t, ts, typ):
        lid[0] += 1
        sg["links"].append({"id": lid[0], "origin_id": o, "origin_slot": os_, "target_id": t, "target_slot": ts, "type": typ})
        return lid[0]

    w = {"tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}
    sg["nodes"].append({
        "id": tid, "type": "VAEDecodeTiled", "title": TILED, "pos": [0, 0], "size": [380, 190], "flags": {"pinned": True},
        "order": 44, "mode": 0,
        "inputs": [{"localized_name": "samples", "name": "samples", "type": "LATENT", "link": None},
                   {"localized_name": "vae", "name": "vae", "type": "VAE", "link": None}]
                  + [{"localized_name": k, "name": k, "type": "INT", "widget": {"name": k}, "link": None} for k in w],
        "outputs": [{"localized_name": "IMAGE", "name": "IMAGE", "type": "IMAGE", "links": None}],
        "properties": {"Node name for S&R": "VAEDecodeTiled", "cnr_id": "comfy-core"},
        "widgets_values": list(w.values()), "widgets_values_named": dict(w)})
    sg["nodes"].append({
        "id": sid, "type": "ComfySwitchNode", "title": SWITCH, "pos": [0, 0], "size": [380, 140], "flags": {"pinned": True},
        "order": 45, "mode": 0,
        "inputs": [{"localized_name": "on_false", "name": "on_false", "shape": 7, "type": "IMAGE", "link": None},
                   {"localized_name": "on_true", "name": "on_true", "shape": 7, "type": "IMAGE", "link": None},
                   {"localized_name": "switch", "name": "switch", "type": "BOOLEAN", "widget": {"name": "switch"}, "link": None}],
        "outputs": [{"localized_name": "output", "name": "output", "type": "IMAGE", "links": None}],
        "properties": {"Node name for S&R": "ComfySwitchNode", "cnr_id": "comfy-core"},
        "widgets_values": [False], "widgets_values_named": {"switch": False}})

    for l in sg["links"]:  # everything that read the plain decoder now reads the switch
        if l["origin_id"] == dec["id"]:
            l["origin_id"], l["origin_slot"] = sid, 0
    lk(src[0]["origin_id"], src[0]["origin_slot"], tid, 0, "LATENT")
    lk(src[1]["origin_id"], src[1]["origin_slot"], tid, 1, "VAE")
    lk(dec["id"], 0, sid, 0, "IMAGE")
    lk(tid, 0, sid, 1, "IMAGE")

    # front-panel toggle after FFN chunking
    at = [i["name"] for i in sg["inputs"]].index(AFTER) + 1
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["origin_slot"] >= at:
            l["origin_slot"] += 1
    tin = {"id": str(uuid.uuid4()), "name": "tiled_on", "type": "BOOLEAN", "linkIds": [lk(-10, at, sid, 2, "BOOLEAN")],
           "label": "tiled VAE decode", "pos": [0, 0]}
    sg["inputs"].insert(at, tin)

    names = [i["name"] for i in outer["inputs"] if i.get("widget")]
    vals = dict(zip(names, outer["widgets_values"]))
    vals["tiled_on"] = False
    oat = [i["name"] for i in outer["inputs"]].index(AFTER) + 1
    outer["inputs"].insert(oat, {"label": "tiled VAE decode", "name": "tiled_on", "type": "BOOLEAN",
                                 "widget": {"name": "tiled_on"}, "link": None})
    for l in d["links"]:
        if l[3] == outer["id"] and l[4] >= oat:
            l[4] += 1
    names = [i["name"] for i in outer["inputs"] if i.get("widget")]
    outer["widgets_values"] = [vals[n] for n in names]
    if "widgets_values_named" in outer:
        outer["widgets_values_named"] = dict(zip(names, outer["widgets_values"]))
    assert [i["name"] for i in outer["inputs"]] == [i["name"] for i in sg["inputs"]]

    # node link fields from the link list
    for n in sg["nodes"]:
        for k, i in enumerate(n["inputs"]):
            hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == k]
            i["link"] = hit[0] if hit else None
        for k, o in enumerate(n.get("outputs", [])):
            hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == k]
            o["links"] = hit or None
    sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], sid)
    sg["state"]["lastLinkId"] = max(sg["state"]["lastLinkId"], lid[0])
    ids = {n["id"] for n in sg["nodes"]} | {-10, -20}
    assert all(l["origin_id"] in ids and l["target_id"] in ids for l in sg["links"])
    for s_, i in enumerate(sg["inputs"]):
        assert all(l["origin_slot"] == s_ for l in sg["links"] if l["id"] in i["linkIds"]), i["name"]

    note = [n for n in d["nodes"] if n["type"] == "MarkdownNote"][0]
    t = note["widgets_values"][0]
    a = [l for l in t.splitlines(True) if l.startswith("- **FFN chunking**")]
    assert len(a) == 1, "Guide has no FFN chunking line"
    note["widgets_values"][0] = t.replace(
        a[0], a[0] + "- **tiled VAE decode**: off · on if the run fails with out-of-memory at the decode step (0.8 MP and up)\n")

    open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
    print("tiled VAE decode added:", path.replace("\\", "/").split("/")[-1])
