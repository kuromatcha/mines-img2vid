"""Stitch video clips into one video through the running ComfyUI, optionally as a seamless loop.

Usage: python -I tools/dasiwa_stitch.py <clip> [<clip> ...] [options]

Clips are joined in the order given, each pair cross-faded over a few frames (the same join the Long
workflows use). By default the result is then passed through DaSiWa's "Seamless Loop" node, which finds
the best loop point and morphs the end into the start with RIFE, so the video repeats without a jump.

A clip can be a full path, a file name in the output/video, output or input folder, or a glob such as
"idle9_*_00001_.mp4" (sorted by name). Clips outside the input and output folders are copied to
input/stitch first. Clips of a different size are scaled to the first clip's size; the first clip's fps is used.

Options:
  -o, --prefix PREFIX   output prefix inside the output folder (default video/stitched)
  --overlap N           frames cross-faded at each join (default 5; 1 with --mode cut = straight cut)
  --mode MODE           linear_blend (default), ease_in_out, filmic_crossfade, perceptual_crossfade, cut
  --no-loop             only join the clips, no seamless loop
  --rtx                 morph the loop point with RTX Frame Generation instead of RIFE
  --server URL          ComfyUI address (default http://127.0.0.1:8188)
  --shared DIR          folder holding ComfyUI's input and output folders (default D:/Comfy-Desktop/ComfyUI-Shared)
  --dry-run             print the graph instead of queueing it

Prints the saved file's path when done. Needs ComfyUI running with ComfyUI-DaSiWa-Nodes installed.
"""
import argparse, glob, json, os, shutil, sys, time, urllib.request, uuid

import av

p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
p.add_argument("clips", nargs="+")
p.add_argument("-o", "--prefix", default="video/stitched")
p.add_argument("--overlap", type=int, default=5)
p.add_argument("--mode", default="linear_blend",
               choices=["linear_blend", "ease_in_out", "filmic_crossfade", "perceptual_crossfade", "cut"])
p.add_argument("--no-loop", action="store_true")
p.add_argument("--rtx", action="store_true")
p.add_argument("--server", default="http://127.0.0.1:8188")
p.add_argument("--shared", default="D:/Comfy-Desktop/ComfyUI-Shared")
p.add_argument("--dry-run", action="store_true")
a = p.parse_args()

INPUT, OUTPUT = (os.path.normpath(os.path.join(a.shared, f)) for f in ("input", "output"))


def find(arg):
    for base in ("", os.path.join(OUTPUT, "video"), OUTPUT, INPUT):
        hits = sorted(glob.glob(os.path.join(base, arg) if base else arg))
        hits = [h for h in hits if os.path.isfile(h)]
        if hits:
            return [os.path.normpath(os.path.abspath(h)) for h in hits]
    sys.exit(f"clip not found: {arg}")


def comfy_name(path):
    """The name LoadVideo accepts: relative to input, or 'rel [output]'. Copies other files into input/stitch."""
    for root, tag in ((INPUT, ""), (OUTPUT, " [output]")):
        if os.path.commonpath([path, root]) == root:
            return os.path.relpath(path, root).replace("\\", "/") + tag
    dst = os.path.join(INPUT, "stitch", os.path.basename(path))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(path, dst)
    return "stitch/" + os.path.basename(path)


def probe(path):
    with av.open(path) as c:
        s = c.streams.video[0]
        return s.codec_context.width, s.codec_context.height, float(s.average_rate or 0), s.frames


clips = [c for arg in a.clips for c in find(arg)]
info = [probe(c) for c in clips]
W, H, fps = info[0][0], info[0][1], info[0][2]
for c, (w, h, f, n) in zip(clips, info):
    note = [] if (w, h) == (W, H) else [f"scaled to {W}x{H}"]
    note += [] if abs(f - fps) < 0.01 else [f"fps {f:g} played at {fps:g}"]
    print(f"  {os.path.basename(c)}  {w}x{h}  {f:g} fps  {n} frames  {' · '.join(note)}")
if a.overlap >= min(n for *_, n in info if n):
    sys.exit("--overlap is longer than a clip")

g, nid = {}, iter(range(1, 10_000))


def node(cls, **inputs):
    k = str(next(nid))
    g[k] = {"class_type": cls, "inputs": inputs}
    return k


frames = None
for c, (w, h, *_) in zip(clips, info):
    v = node("LoadVideo", file=comfy_name(c))
    img = [node("GetVideoComponents", video=[v, 0]), 0]
    if (w, h) != (W, H):
        img = [node("ImageScale", image=img, upscale_method="lanczos", width=W, height=H, crop="center"), 0]
    frames = img if frames is None else [node(
        "ImageBatchExtendWithOverlap", source_images=frames, new_images=img, overlap=a.overlap,
        overlap_side="source", overlap_mode=a.mode), 2]
if not a.no_loop:
    frames = [node("DaSiWa_SeamlessLoop", images=frames, model_name="rife_v4.26.safetensors", exact_endpoint=False,
                   interpolation_backend="RTX Frame Generation" if a.rtx else "RIFE / FILM", rtx_mode="HIGH",
                   rtx_device_id=0, frame_rate=fps, audio_loop="Crossfade"), 0]
video = node("CreateVideo", images=frames, fps=fps, bit_depth="auto", color_space="sRGB")
save = node("SaveVideo", video=[video, 0], filename_prefix=a.prefix, format="auto", **{"format.codec": "auto"})

if a.dry_run:
    print(json.dumps(g, indent=1))
    sys.exit()

req = urllib.request.Request(a.server + "/prompt", json.dumps({"prompt": g, "client_id": str(uuid.uuid4())}).encode(),
                             {"Content-Type": "application/json"})
try:
    pid = json.load(urllib.request.urlopen(req))["prompt_id"]
except urllib.error.HTTPError as e:
    sys.exit(f"ComfyUI refused the graph: {e.read().decode()[:2000]}")
except urllib.error.URLError as e:
    sys.exit(f"ComfyUI is not reachable at {a.server}: {e.reason}")
print(f"queued {pid}", flush=True)
t0 = time.time()
while True:
    time.sleep(2)
    h = json.load(urllib.request.urlopen(f"{a.server}/history/{pid}")).get(pid)
    if h and h.get("status", {}).get("completed") is not None:
        break
st = h["status"]
if st["status_str"] != "success":
    err = [m[1] for m in st["messages"] if m[0] == "execution_error"]
    sys.exit(f"failed: {json.dumps(err)[:2000]}")
out = h["outputs"].get(save, {})
for f in out.get("images", []) + out.get("videos", []):
    path = os.path.join(OUTPUT, f.get("subfolder", ""), f["filename"])
    with av.open(path) as c:
        n = c.streams.video[0].frames
    print(f"saved {os.path.normpath(path)}  ({n} frames, {n / fps:.1f} s, took {time.time() - t0:.0f} s)")
