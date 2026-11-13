"""Plain names plus one guide note, instead of tips packed into names.

- Front panel: setting labels are the bare setting name (no ranges, defaults or advice in brackets).
- Inside the subgraph: node titles say literally what the node does.
- All advice moves to a single Markdown note ("Guide") beside the video output.
Run last. Safe to run again: it replaces the labels, titles and the guide note.
"""
import json, sys

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
loop = any(n["type"] == "DaSiWa_SeamlessLoop" for n in sg["nodes"])

# Settings that never change for this distilled model leave the front panel; the value stays on the node inside.
# steps (4), split step (2), seed (random on every run), cfg (1), shift (5), sampler, scheduler, NAG, NAG scale
HIDE = ["value_2", "value_3", "noise_seed", "cfg", "shift", "sampler_name", "scheduler", "nag_on", "nag_scale",
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
    "chunk_on": "FFN chunking", "strength": "color match strength", "switch": "model upscale",
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

Load an image, write a prompt, run. Defaults are the model developer's.

## Prompt
- One paragraph, 80–120 words: **subject → motion → camera → scene**.
- Name the subject briefly; the image shows the rest. Spend the words on motion.
- One continuous action, one camera move (or a still camera).
{"- For a loop, describe a repeating motion that ends in the pose it started in." if loop else "- Use the Loop workflow when the clip should end where it started."}
- **negative prompt** only works with NAG on or cfg above 1 (both inside the subgraph, see below).

## Size and length
- **megapixels**: 0.3 quick test · 0.6 normal · 0.8 high (turn **FFN chunking** on).
- **duration (seconds)**: 5 is the model's native length; longer clips drift.
- **fps**: 16, or 24 for faster motion.

## Sampling (inside the subgraph)
These follow the model developer and are not on the front panel. Open the subgraph to change them.
- Steps 4, split step 2, cfg 1, shift 5, euler / simple.
- The seed is random on every run. To repeat a result, on *Sample high-noise steps* set the seed and switch *control after generate* to fixed.
- NAG makes the negative prompt work at cfg 1 (e.g. to stop mouth movement) and uses more VRAM. To turn it on, set both *Switch: NAG (high)* and *Switch: NAG (low)* to true.

## Model files (inside the subgraph)
Pick the files on the loader nodes: *Load high-noise model*, *Load low-noise model*, *Load text encoder*, *Load VAE*, *Load upscale model*, *Load interpolation model*.

## Memory
- **FFN chunking**: lowers peak VRAM, slightly slower. Use from 0.7 megapixels up on 16 GB.

## After sampling
- **color match strength**: {"0.75 keeps the loop from washing out or flashing at the loop point." if loop else "0 is off. 0.75 pulls colors back to the start image."}
- **model upscale**: doubles each side with AnimeSharpV4. Slow, sharp lines.
- **RTX upscale**: doubles each side with NVIDIA RTX Video Super Resolution. Fast, mild. Replaces the model upscale when both are on. Needs the `nvidia-vfx` package.
- **interpolation multiplier**: 1 is off, 2 doubles the fps{" (the loop stays seamless)" if loop else ""}.

## Routine
1. Test at 0.3 megapixels, 3 seconds, everything under *After sampling* off.
2. Change the prompt, or just run again for a new seed, until the motion is right.
3. Render the final at 0.6 megapixels, 5 seconds, then add upscale or interpolation. Fix the seed inside the subgraph first if you want the same motion.

Out of memory: turn FFN chunking on or lower megapixels, then restart ComfyUI.
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
