"""UI clean-up for the DaSiWa workflows: short names, grid layout, sized groups, logical setting order.
Wiring is not changed (checked before/after)."""
import json, sys

TITLE = {
    95: "High-noise model", 96: "Low-noise model", 84: "Text encoder", 90: "VAE",
    188: "Attention · high", 189: "Attention · low",
    190: "Chunk FFN · high", 191: "Chunk FFN · low",
    192: "Chunking on/off · high", 193: "Chunking on/off · low",
    186: "Scale image", 187: "Image size",
    93: "Prompt", 89: "Negative prompt",
    161: "Duration (s)", 162: "FPS", 163: "Frame count", 170: "Output FPS",
    118: "Steps", 124: "Split step", 122: "CFG",
    104: "Shift · high", 176: "NAG · high", 178: "NAG on/off · high", 86: "Sampler · high",
    103: "Shift · low", 177: "NAG · low", 179: "NAG on/off · low", 85: "Sampler · low",
    87: "Decode", 171: "Color match", 172: "Seamless loop",
    173: "Upscale model", 174: "Upscale", 175: "Upscale on/off",
    169: "Interpolate (RIFE)", 94: "Create video",
}
# groups: title, list of columns, each column = (width, [node ids top to bottom])
GROUPS = [
    ("1 · Models", [(380, [95, 96, 84, 90]), (380, [188, 190, 192, 189, 191, 193])]),
    ("2 · Input", [(520, [186, 187, 93, 89, 98])]),
    ("3 · Timing", [(380, [161, 162, 163, 170])]),
    ("4 · Sampling", [(380, [118, 124, 122])]),
    ("5 · High noise", [(380, [104, 176, 178, 86])]),
    ("6 · Low noise", [(380, [103, 177, 179, 85])]),
    ("7 · Output", [(380, [87, 171, 172]), (380, [173, 174, 175, 169, 94])]),
]
ORDER = ["start_image", "text", "text_1", "megapixels", "value_1", "value_4", "noise_seed",
         "value_2", "value_3", "cfg", "shift", "sampler_name", "scheduler",
         "nag_on", "nag_scale", "chunk_on", "strength", "switch", "model_name", "multiplier", "ckpt_name"]
LABEL = {
    "text": "prompt", "text_1": "negative prompt",
    "megapixels": "megapixels (0.3 test · 0.6 base · 0.8 HD)",
    "value_1": "duration (s)", "value_4": "fps", "noise_seed": "seed",
    "value_2": "steps", "value_3": "split step", "cfg": "cfg", "shift": "shift",
    "sampler_name": "sampler", "scheduler": "scheduler",
    "nag_on": "NAG (negative prompt at cfg 1)", "nag_scale": "NAG scale",
    "chunk_on": "FFN chunking (for 0.7+ MP)",
    "strength": "color match (0 = off)", "switch": "upscale", "model_name": "upscale model",
    "multiplier": "interpolation × (1 = off)", "ckpt_name": "interpolation model",
}
GAP_COL, GAP_GROUP, GAP_NODE, TITLE_H, PAD, HEADER = 30, 80, 24, 30, 20, 46


def wiring(d):
    sg = d["definitions"]["subgraphs"][0]
    ins = [i["name"] for i in sg["inputs"]]
    return sorted((str(ins[l["origin_slot"]] if l["origin_id"] == -10 else l["origin_id"]), l["origin_slot"] if l["origin_id"] != -10 else 0, l["target_id"],
                   [i["name"] for i in {n["id"]: n for n in sg["nodes"]}[l["target_id"]]["inputs"]][l["target_slot"]]
                   if l["target_id"] != -20 else "OUT") for l in sg["links"])


def tidy(path, loop):
    d = json.load(open(path, encoding="utf-8"))
    before = wiring(d)
    sg = d["definitions"]["subgraphs"][0]
    nodes = {n["id"]: n for n in sg["nodes"]}
    outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]

    # titles
    for nid, t in TITLE.items():
        if nid in nodes:
            nodes[nid]["title"] = t
    nodes[98]["title"] = "Latent (first = last frame)" if loop else "Latent (start frame)"
    placed = {nid for _, cols in GROUPS for _, col in cols for nid in col}
    missing = set(nodes) - placed
    assert not missing, f"unplaced nodes: {missing}"

    # grid layout
    x, y0 = 0, 0
    boxes = []
    for gtitle, cols in GROUPS:
        gx = x
        bottom = y0
        for width, col in cols:
            y = y0
            for nid in col:
                if nid not in nodes:
                    continue
                n = nodes[nid]
                n["pos"] = [x, y]
                n["size"] = [width, n["size"][1]]
                n.get("flags", {}).pop("collapsed", None)
                y += n["size"][1] + TITLE_H + GAP_NODE
                bottom = max(bottom, y - GAP_NODE)
            x += width + GAP_COL
        x -= GAP_COL
        boxes.append([gtitle, gx, x, bottom])
        x += GAP_GROUP
    max_bottom = max(b[3] for b in boxes)
    sg["groups"] = [{"id": k + 1, "title": t, "bounding": [gx - PAD, y0 - TITLE_H - HEADER, (gr - gx) + 2 * PAD,
                     (max_bottom - y0) + TITLE_H + HEADER + PAD], "color": "#3f789e", "font_size": 24, "flags": {}}
                    for k, (t, gx, gr, _) in enumerate(boxes)]
    sg["state"]["lastGroupId"] = len(boxes)
    sg["inputNode"]["bounding"] = [-PAD - 60 - 300, y0, 300, sg["inputNode"]["bounding"][3]]
    sg["outputNode"]["bounding"] = [x - GAP_GROUP + PAD + 60, y0, 128, 68]

    # front settings: logical order + short labels
    by = {i["name"]: i for i in sg["inputs"]}
    assert set(by) == set(ORDER), set(by) ^ set(ORDER)
    old_slot = {i["name"]: k for k, i in enumerate(sg["inputs"])}
    sg["inputs"] = [by[n] for n in ORDER]
    new_slot = {n: k for k, n in enumerate(ORDER)}
    names_old = list(old_slot)
    for l in sg["links"]:
        if l["origin_id"] == -10:
            l["origin_slot"] = new_slot[names_old[l["origin_slot"]]]
    for i in sg["inputs"]:
        if i["name"] in LABEL:
            i["label"] = LABEL[i["name"]]
    oby = {i["name"]: i for i in outer["inputs"]}
    vals = dict(zip([i["name"] for i in outer["inputs"] if i.get("widget")], outer["widgets_values"]))
    outer["inputs"] = [oby[n] for n in ORDER]
    for i in outer["inputs"]:
        if i["name"] in LABEL:
            i["label"] = LABEL[i["name"]]
    wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
    outer["widgets_values"] = [vals[n] for n in wn]
    outer["widgets_values_named"] = dict(zip(wn, outer["widgets_values"]))

    # top level: image -> settings -> video, aligned in one row
    top = {n["type"]: n for n in d["nodes"]}
    top["LoadImage"]["pos"], top["LoadImage"]["size"] = [0, 0], [440, 640]
    outer["pos"], outer["size"] = [480, 0], [560, outer["size"][1]]
    top["SaveVideo"]["pos"], top["SaveVideo"]["size"] = [1080, 0], [560, 640]
    top["LoadImage"]["title"], top["SaveVideo"]["title"] = "Start image", "Video"
    d.get("extra", {}).pop("ds", None)

    assert wiring(d) == before, "wiring changed"
    for slot, i in enumerate(sg["inputs"]):
        for lid in i["linkIds"]:
            assert [l for l in sg["links"] if l["id"] == lid][0]["origin_slot"] == slot
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print("tidied", path.split("/")[-1], "| groups:", [(b[0], b[2] - b[1]) for b in boxes], "| height", max_bottom)


for p in sys.argv[1:]:
    tidy(p, loop="Loop" in p)
