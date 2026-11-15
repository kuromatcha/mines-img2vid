"""Layout pass for the WAN workflows (I2V, Loop, Long, Painter).

Usage: python -I tools/dasiwa_layout.py <workflow> [<workflow> ...]

- Front panel: a "shift" setting (after fps) drives both Set shift nodes, high and low, which must match.
- Subgraph: every node is placed by its title into a group of tidy columns (data flows left to right),
  one group per stage. Rows line up across a group's columns, all groups share one bottom edge, and
  everything sits on the 20 px snap grid. Long workflows get one group per extra segment.
  Fails if a node has no place, so new nodes cannot end up stacked on top of others.
- Top level: one top-aligned row: start image, end image(s), settings, video, Guide.
Wiring is checked before and after: only the new shift links are added. Run it last; safe to run again.
"""
import json, re, sys, uuid

# Positions and sizes sit on ComfyUI's 20 px snap grid (title bar 30 + gap 30 = 60 between stacked nodes),
# so a node dragged by hand snaps back into line.
GAP_COL, GAP_GROUP, GAP_NODE, TITLE_H, PAD, HEADER = 40, 80, 30, 30, 20, 50
W = 380


def snap(v, grid=20):
    return -(-int(round(v)) // grid) * grid

MODELS = ("1 · Models", [
    ["Load high-noise model", "Load low-noise model", "Load text encoder", "Load VAE"],
    ["Apply SVI LoRA (high)", "Set attention backend (high)",
     "Chunk feed-forward (high)", "Switch: FFN chunking (high)"],
    ["Apply SVI LoRA (low)", "Set attention backend (low)",
     "Chunk feed-forward (low)", "Switch: FFN chunking (low)"],
])
INPUT = ("2 · Input", [["Scale image to megapixels", "Get image width and height", "Encode start image (anchor)",
                        "Encode prompt", "Encode prompt 1", "Encode negative prompt",
                        "Build latent from start and end image", "Build latent from start image (Painter)", "Build latent from first and last frame (Painter)",
                        "Build latent from first and last frame",
                        "Build segment 1 latent (SVI)"]])
TIMING = ("3 · Timing", [["Duration in seconds", "Frames per second", "Calculate frame count", "Calculate output fps"]])
SAMPLING = ("4 · Sampling", [["Total steps", "Split step", "CFG"]])
HIGH = ("5 · High noise", [["Set shift (high)", "Apply NAG (high)", "Switch: NAG (high)",
                            "Sample high-noise steps", "Sample high-noise steps (segment 1)"]])
LOW = ("6 · Low noise", [["Set shift (low)", "Apply NAG (low)", "Switch: NAG (low)",
                          "Sample low-noise steps", "Sample low-noise steps (segment 1)", "Decode segment 1"]])
OUTPUT = [
    ("Decode", [["Decode latent to frames", "Fix color drift", "Match colors to start image", "Make loop seamless"]]),
    ("Upscale", [["Load upscale model", "Upscale with model", "Switch: model upscale"],
                 ["Upscale with RTX VSR", "Keep colors after RTX", "Switch: RTX upscale"]]),
    ("Interpolate", [["Interpolation multiplier", "Clamp multiplier to 2 or more", "Is multiplier above 1?"],
                     ["Load interpolation model", "Interpolate frames", "Switch: interpolation"]]),
    ("Video", [["Count frames", "Subtract 1 from frame count", "Remove repeated first frame", "Create video"]]),
]
STACK = ("Upscale",)  # groups whose columns are separate paths: no row alignment


def segment(k):
    return (f"Segment {k}", [[f"Encode prompt {k}", f"Build segment {k} latent (SVI)",
                              f"Sample high-noise steps (segment {k})", f"Sample low-noise steps (segment {k})",
                              f"Decode segment {k}", f"Join segment {k}"]])


def wiring(sg):
    ins = [i["name"] for i in sg["inputs"]]
    nodes = {n["id"]: n for n in sg["nodes"]}
    return sorted((ins[l["origin_slot"]] if l["origin_id"] == -10 else str(l["origin_id"]),
                   0 if l["origin_id"] == -10 else l["origin_slot"], l["target_id"],
                   "OUT" if l["target_id"] == -20 else nodes[l["target_id"]]["inputs"][l["target_slot"]]["name"])
                  for l in sg["links"])


def add_shift(d, sg, outer):
    if "shift" in [i["name"] for i in sg["inputs"]]:
        return False
    T = {n.get("title"): n for n in sg["nodes"]}
    targets = [T["Set shift (high)"], T["Set shift (low)"]]
    value = targets[0]["widgets_values"][0]
    assert all(n["widgets_values"][0] == value for n in targets), "high and low shift differ"
    at = [i["name"] for i in sg["inputs"]].index("value_4") + 1  # after fps
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["origin_slot"] >= at:
            l["origin_slot"] += 1
    ids = []
    for n in targets:
        sg["state"]["lastLinkId"] += 1
        lid = sg["state"]["lastLinkId"]
        slot = [i["name"] for i in n["inputs"]].index("shift")
        assert n["inputs"][slot]["link"] is None
        n["inputs"][slot]["link"] = lid
        sg["links"].append({"id": lid, "origin_id": -10, "origin_slot": at, "target_id": n["id"],
                            "target_slot": slot, "type": "FLOAT"})
        ids.append(lid)
    sg["inputs"].insert(at, {"id": str(uuid.uuid4()), "name": "shift", "type": "FLOAT", "linkIds": ids,
                             "localized_name": "shift", "label": "shift", "pos": [0, 0]})
    # outer node: same input order, widget value after fps
    names = [i["name"] for i in outer["inputs"] if i.get("widget")]
    vals = dict(zip(names, outer["widgets_values"]))
    oat = [i["name"] for i in outer["inputs"]].index("value_4") + 1
    outer["inputs"].insert(oat, {"localized_name": "shift", "label": "shift", "name": "shift", "type": "FLOAT",
                                 "widget": {"name": "shift"}, "link": None})
    for l in d["links"]:
        if l[3] == outer["id"] and l[4] >= oat:
            l[4] += 1
    vals["shift"] = value
    names = [i["name"] for i in outer["inputs"] if i.get("widget")]
    outer["widgets_values"] = [vals[n] for n in names]
    if "widgets_values_named" in outer:
        outer["widgets_values_named"] = dict(zip(names, outer["widgets_values"]))
    assert [i["name"] for i in outer["inputs"]] == [i["name"] for i in sg["inputs"]]
    return True


def guide(d):
    note = [n for n in d["nodes"] if n["type"] == "MarkdownNote"][0]
    t = note["widgets_values"][0]
    line = "- **shift**: 5 · higher = bigger motion and layout change, lower = closer to the start image (dev: 5–10)\n"
    if "**shift**" not in t:
        a = [l for l in t.splitlines(True) if l.startswith("- **fps**")]
        assert len(a) == 1
        t = t.replace(a[0], a[0] + line)
    t = t.replace(" · shift 5 · ", " · ")
    note["widgets_values"][0] = t


def layout(sg):
    nodes = {n.get("title"): n for n in sg["nodes"]}
    assert len(nodes) == len(sg["nodes"]), "duplicate titles"
    segs = sorted(int(m.group(1)) for t in nodes for m in [re.fullmatch(r"Join segment (\d+)", t or "")] if m)
    plan = [MODELS, INPUT, TIMING, SAMPLING, HIGH, LOW] + [segment(k) for k in segs]
    n_main = 6
    for k, (t, cols) in enumerate(OUTPUT):
        plan.append((f"{n_main + k + 1} · {t}", cols))
    placed = [t for _, cols in plan for col in cols for t in col if t in nodes]
    missing = set(nodes) - set(placed)
    assert not missing, f"no place for: {sorted(missing)}"
    assert len(placed) == len(set(placed))

    x, y0, groups = 0, 0, []
    for gtitle, cols in plan:
        cols = [[nodes[t] for t in col if t in nodes] for col in cols]
        cols = [c for c in cols if c]
        if not cols:
            continue
        for c in cols:
            for n in c:
                n.get("flags", {}).pop("collapsed", None)
                n["size"] = [snap(n["size"][0]), snap(n["size"][1])]
        # rows line up across the columns of a group (each row as tall as its tallest node), except in groups
        # whose columns are separate paths, where one tall node would push the other column far down
        if gtitle.endswith(STACK):
            tops = [[y0 + sum(n["size"][1] for n in c[:r]) + r * (TITLE_H + GAP_NODE) for r in range(len(c))]
                    for c in cols]
        else:
            heights = [max(c[r]["size"][1] for c in cols if r < len(c)) for r in range(max(map(len, cols)))]
            tops = [[y0 + sum(heights[:r]) + r * (TITLE_H + GAP_NODE) for r in range(len(c))] for c in cols]
        gx, bottom = x, y0
        for c, ct in zip(cols, tops):
            width = max([W] + [n["size"][0] for n in c])
            for n, top in zip(c, ct):
                n["pos"], n["size"] = [x, top], [width, n["size"][1]]
                bottom = max(bottom, top + n["size"][1])
            x += width + GAP_COL
        right = x - GAP_COL
        groups.append({"id": len(groups) + 1, "title": gtitle,
                       "bounding": [gx - PAD, y0 - TITLE_H - HEADER, right - gx + 2 * PAD,
                                    bottom - y0 + TITLE_H + HEADER + PAD],
                       "color": "#3f789e", "font_size": 24, "flags": {}})
        x = right + GAP_GROUP
    tallest = max(g["bounding"][3] for g in groups)  # one even bottom edge for all groups
    for g in groups:
        g["bounding"][3] = tallest
    sg["groups"] = groups
    sg["state"]["lastGroupId"] = len(groups)
    sg["inputNode"]["bounding"] = [-PAD - 60 - 300, y0, 300, sg["inputNode"]["bounding"][3]]
    sg["outputNode"]["bounding"] = [x - GAP_GROUP + PAD + 60, y0, 128, 68]
    return [(g["title"], g["bounding"][2], g["bounding"][3]) for g in groups]


# Front panel: one row, every node the same height, widths and gaps on ComfyUI's 20 px snap grid.
# Image loaders and the video player share one width, so the start image, end image(s) and the finished
# video preview at the same size. Settings is wider and as tall as the row, which gives each prompt box
# about 280 px (about 15 lines) on I2V and Loop.
FRONT_H, FRONT_GAP = 960, 40
FRONT_W = {"image": 480, "settings": 640, "video": 480, "guide": 560}


def front(d, sg):
    outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
    top = {n["type"]: n for n in d["nodes"]}
    start = top["LoadImage"]
    ends = sorted((n for n in d["nodes"] if n["type"] == "MinesLoadImageOptional"), key=lambda n: n["title"])
    row = [(n, "image") for n in [start] + ends] + [(outer, "settings"), (top["SaveVideo"], "video"),
                                                   (top["MarkdownNote"], "guide")]
    assert len(row) == len(d["nodes"]), "unplaced front-panel node"
    x = 0
    for n, kind in row:
        n["pos"], n["size"] = [x, 0], [FRONT_W[kind], FRONT_H]
        x += FRONT_W[kind] + FRONT_GAP
    d.get("extra", {}).pop("ds", None)
    return outer


for path in sys.argv[1:]:
    d = json.load(open(path, encoding="utf-8"))
    sg = d["definitions"]["subgraphs"][0]
    outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
    before = wiring(sg)
    added = add_shift(d, sg, outer)
    guide(d)
    after = wiring(sg)
    new = [w for w in after if w not in before]
    assert all(w[0] == "shift" for w in new) and len(after) - len(before) == (2 if added else 0), new
    assert set(before) <= set(after)
    groups = layout(sg)
    front(d, sg)
    assert wiring(sg) == after, "layout changed wiring"
    for s_, i in enumerate(sg["inputs"]):
        assert i["linkIds"] and all(l["origin_slot"] == s_ for l in sg["links"] if l["id"] in i["linkIds"]), i["name"]
    open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
    print(path.replace("\\", "/").split("/")[-1], "| shift added" if added else "| shift already there", "|",
          ", ".join(f"{t} {w}x{h}" for t, w, h in groups))
