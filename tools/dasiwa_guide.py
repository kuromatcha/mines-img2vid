"""Plain names plus one guide note, instead of tips packed into names.

- Front panel: setting labels are the bare setting name (no ranges, defaults or advice in brackets).
- Inside the subgraph: node titles say literally what the node does.
- All advice moves to a single Markdown note ("Guide") beside the video output.
Run last. Safe to run again: it replaces the labels, titles and the guide note.
"""
import json, sys, uuid

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
loop = any(n["type"] == "DaSiWa_SeamlessLoop" for n in sg["nodes"])

# Settings that never change for this distilled model leave the front panel; the value stays on the node inside.
# steps (4), split step (2), seed (random on every run), cfg (1), shift (5), sampler, scheduler, NAG scale
HIDE = ["value_2", "value_3", "noise_seed", "cfg", "shift", "sampler_name", "scheduler", "nag_scale",
        "model_name", "ckpt_name"]  # upscale model and interpolation model files are picked on their loader nodes
for name in HIDE:
    names = [i["name"] for i in sg["inputs"]]
    if name not in names:
        continue
    slot = names.index(name)
    gone = set(sg["inputs"][slot]["linkIds"])
    sg["links"] = [l for l in sg["links"] if l["id"] not in gone]
    del sg["inputs"][slot]
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["origin_slot"] > slot:
            l["origin_slot"] -= 1
    for n in sg["nodes"]:
        for i in n["inputs"]:
            if i.get("link") in gone:
                i["link"] = None
    wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
    vals = dict(zip(wn, outer["widgets_values"]))
    vals.pop(name)
    outer["inputs"] = [i for i in outer["inputs"] if i["name"] != name]
    outer["widgets_values"] = list(vals.values())
    outer["widgets_values_named"] = dict(vals)
# NAG on/off stays on the front panel as "negative" (it decides whether the negative prompt does anything).
# Re-add it if an earlier run of this script hid it: one toggle driving both NAG switches.
if "nag_on" not in [i["name"] for i in sg["inputs"]]:
    nag_sw = [n for n in sg["nodes"] if n["type"] == "ComfySwitchNode"
              and (n.get("title") or "").startswith(("Switch: NAG", "NAG on/off"))]
    assert len(nag_sw) == 2, "expected the two NAG switches"
    names = [i["name"] for i in sg["inputs"]]
    pos = next((k for k, i in enumerate(sg["inputs"]) if i["type"] == "BOOLEAN"), len(names))
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["origin_slot"] >= pos:
            l["origin_slot"] += 1
    tin = {"id": str(uuid.uuid4()), "name": "nag_on", "type": "BOOLEAN", "linkIds": [], "label": "negative", "pos": [0, 0]}
    sg["inputs"].insert(pos, tin)
    lid = max(l["id"] for l in sg["links"])
    for n in nag_sw:
        lid += 1
        k = [j for j, i in enumerate(n["inputs"]) if i["name"] == "switch"][0]
        assert n["inputs"][k]["link"] is None
        sg["links"].append({"id": lid, "origin_id": -10, "origin_slot": pos, "target_id": n["id"], "target_slot": k, "type": "BOOLEAN"})
        n["inputs"][k]["link"] = lid
        tin["linkIds"].append(lid)
    sg["state"]["lastLinkId"] = max(sg["state"]["lastLinkId"], lid)
    wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
    vals = dict(zip(wn, outer["widgets_values"]))
    vals["nag_on"] = False
    after = sg["inputs"][pos - 1]["name"] if pos else None
    at = [i["name"] for i in outer["inputs"]].index(after) + 1 if after else 0
    outer["inputs"].insert(at, {"label": "negative", "name": "nag_on", "type": "BOOLEAN", "widget": {"name": "nag_on"}, "link": None})
    wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
    outer["widgets_values"] = [vals[n] for n in wn]
    outer["widgets_values_named"] = {n: vals[n] for n in wn}
# Front panel order: values first, on/off toggles together at the bottom (stable within each group).
wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
vals = dict(zip(wn, outer["widgets_values"]))
order = sorted(range(len(sg["inputs"])), key=lambda k: sg["inputs"][k]["type"] == "BOOLEAN")
sg["inputs"] = [sg["inputs"][k] for k in order]
by_name = {i["name"]: i for i in outer["inputs"]}
outer["inputs"] = [by_name[i["name"]] for i in sg["inputs"]]
for slot, i in enumerate(sg["inputs"]):
    for l in sg["links"]:
        if l["id"] in i["linkIds"]:
            l["origin_slot"] = slot
wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
outer["widgets_values"] = [vals[n] for n in wn]
outer["widgets_values_named"] = {n: vals[n] for n in wn}
for slot, i in enumerate(sg["inputs"]):
    for x in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == x][0]["origin_slot"] == slot, i["name"]
for n in sg["nodes"]:  # hidden settings keep the developer defaults on the nodes inside
    if n["type"] == "ModelSamplingSD3":
        n["widgets_values"] = [5.0]
        n["widgets_values_named"] = {"shift": 5.0}
for n in sg["nodes"]:  # with the seed off the front panel, the sampler draws a new one each run
    if n["type"] == "KSamplerAdvanced" and n["widgets_values"][0] == "enable":
        n["widgets_values"][2] = "randomize"
        if "widgets_values_named" in n and "control_after_generate" in n["widgets_values_named"]:
            n["widgets_values_named"]["control_after_generate"] = "randomize"

LABELS = {
    "text": "prompt", "text_1": "negative prompt", "megapixels": "megapixels", "value_1": "duration (seconds)",
    "value_4": "fps",
    "nag_on": "negative", "chunk_on": "FFN chunking", "strength": "color match strength", "switch": "model upscale",
    "rtx_on": "RTX upscale", "multiplier": "interpolation multiplier",
}
for i in sg["inputs"] + outer["inputs"]:
    if i["name"] in LABELS:
        i["label"] = LABELS[i["name"]]
assert {i["name"] for i in sg["inputs"]} - {"start_image"} == set(LABELS), "front panel settings changed"

# (node type, which model the node sits on or None) -> title; math and switch nodes are matched by what feeds them
BY_TYPE = {
    "UNETLoader": "Load {m}-noise model", "UnetLoaderGGUF": "Load {m}-noise model",
    "CLIPLoader": "Load text encoder", "VAELoader": "Load VAE",
    "ModelAttentionBackend": "Set attention backend ({m})", "WanChunkFeedForward": "Chunk feed-forward ({m})",
    "ModelSamplingSD3": "Set shift ({m})", "NAGuidance": "Apply NAG ({m})",
    "KSamplerAdvanced": "Sample {m}-noise steps",
    "ImageScaleToTotalPixels": "Scale image to megapixels", "WanImageToVideo": "Build latent from start image",
    "WanFirstLastFrameToVideo": "Build latent from first and last frame",
    "VAEDecode": "Decode latent to frames", "ColorTransfer": "Match colors to start image",
    "DaSiWa_SeamlessLoop": "Make loop seamless", "UpscaleModelLoader": "Load upscale model",
    "ImageUpscaleWithModel": "Upscale with model", "DaSiWa_RTX_UpscalerRefiner": "Upscale with RTX VSR",
    "FrameInterpolationModelLoader": "Load interpolation model", "FrameInterpolate": "Interpolate frames",
    "ImageFromBatch": "Remove repeated first frame", "CreateVideo": "Create video",
}
BY_OLD = {  # nodes whose type alone does not say what they do
    "Prompt": "Encode prompt", "Negative prompt": "Encode negative prompt",
    "Image size": "Get image width and height", "Frame count (with repeated first frame)": "Count frames",
    "Duration (s)": "Duration in seconds", "FPS": "Frames per second", "Steps": "Total steps",
    "Split step": "Split step", "CFG": "CFG", "Interpolation multiplier": "Interpolation multiplier",
    "Frame count": "Calculate frame count", "Output FPS": "Calculate output fps",
    "Interpolation × (at least 2)": "Clamp multiplier to 2 or more",
    "Interpolation on? (× above 1)": "Is multiplier above 1?", "Frame count − 1": "Subtract 1 from frame count",
    "Chunking on/off · high": "Switch: FFN chunking (high)", "Chunking on/off · low": "Switch: FFN chunking (low)",
    "NAG on/off · high": "Switch: NAG (high)", "NAG on/off · low": "Switch: NAG (low)",
    "Upscale on/off": "Switch: model upscale", "RTX upscale on/off": "Switch: RTX upscale",
    "Interpolation on/off": "Switch: interpolation",
}
done = set(BY_OLD.values()) | {t.format(m=m) for t in BY_TYPE.values() for m in ("high", "low")}
for n in sg["nodes"]:
    old = n.get("title") or ""
    if old in done:
        continue
    if old in BY_OLD:
        n["title"] = BY_OLD[old]
    elif n["type"] in BY_TYPE:
        m = "high" if "high" in old.lower() else "low" if "low" in old.lower() else ""
        assert m or "{m}" not in BY_TYPE[n["type"]], (n["id"], old)
        n["title"] = BY_TYPE[n["type"]].format(m=m)
    else:
        raise SystemExit(f"no literal title for node {n['id']} {n['type']} {old!r}")

GUIDE = f"""# Guide

## Prompt
- 80–120 words: **subject → motion → camera → scene**.
- Subject in a few words; spend the rest on motion.
- One action, one camera move.
{"- Motion ends in the starting pose." if loop else "- Same start and end pose: use the Loop workflow."}
- Negative prompt works only with **negative** on.

## Settings
- **megapixels**: 0.3 test · 0.6 final · 0.8 high (FFN chunking on)
- **duration (seconds)**: 5. Longer drifts.
- **fps**: 16 · 24 for fast motion
- **color match strength**: {"0.75. Stops the flash at the loop point." if loop else "0 off · 0.75 on"}
- **interpolation multiplier**: 1 off · 2 doubles fps
- **negative**: applies the negative prompt (NAG). Uses more VRAM.
- **FFN chunking**: less VRAM, slower. On from 0.7 MP.
- **model upscale**: 2× AnimeSharp. Slow, sharp.
- **RTX upscale**: 2× RTX VSR. Fast, mild. Overrides model upscale. Needs `nvidia-vfx`.

## Inside the subgraph
- Steps 4 · split 2 · cfg 1 · shift 5 · euler / simple
- Seed: random. To keep one: *Sample high-noise steps* → fixed.
- NAG scale 11: the *Apply NAG* nodes.
- Model files: the *Load …* nodes.

## Routine
1. Test: 0.3 MP, 3 s, extras off.
2. Rerun until the motion is right, then fix the seed.
3. Final: 0.6 MP, 5 s, then upscale / interpolation.

Out of memory: FFN chunking on or lower MP, then restart ComfyUI.
"""

outer["size"] = [outer["size"][0], 640]  # fewer settings: same height as the image and video nodes
d["nodes"] = [n for n in d["nodes"] if n["type"] != "MarkdownNote"]
gid = max(n["id"] for n in d["nodes"]) + 1
save = [n for n in d["nodes"] if n["type"] == "SaveVideo"][0]
d["nodes"].append({"id": gid, "type": "MarkdownNote", "title": "Guide",
                   "pos": [save["pos"][0] + save["size"][0] + 40, save["pos"][1]], "size": [560, 1100],
                   "flags": {}, "order": 0, "mode": 0, "inputs": [], "outputs": [], "properties": {},
                   "widgets_values": [GUIDE], "color": "#432", "bgcolor": "#653"})
d["last_node_id"] = max(d["last_node_id"], gid)

open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("guide + plain names:", path.replace("\\", "/").split("/")[-1])
