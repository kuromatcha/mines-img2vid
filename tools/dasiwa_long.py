"""Long video (SVI 2.0 Pro): N chained 5-second segments, one prompt each, from a finished I2V workflow.

Usage: python -I tools/dasiwa_long.py <finished I2V workflow> <output workflow> <segments>

- SVI 2.0 Pro LoRAs on both models (KJNodes "Wan Image To Video SVIPro" + LoraLoaderModelOnly).
- Every segment is conditioned on the start image (anchor, keeps the character) and on the last latent of the
  previous segment (keeps the motion going), so joints carry momentum instead of restarting from a still frame.
- Every segment has an optional end image (front panel "End image (segment N)", bypassed = skip): the pose that
  segment ends on, placed on its last frame. Needs an I2V workflow from workflows/ (it has the end image input)
  and the SVIPro end frame node from mines-pack (github.com/kuromatcha/mines-pack).
- Each decoded segment after the first starts by replaying the last 5 frames of the previous one; those are
  cross-faded over each other, then everything after the join is the same as the I2V workflow
  (color drift fix, upscale, RTX upscale, interpolation, create video).
"""
import copy, json, sys, uuid

END_LINE = ("- **End image** (optional): the pose the clip ends on, e.g. the front view after a turn. "
            "Bypassed (Ctrl+B) = skip. Keep framing, background and style the same as the start image.\n")

src, dst, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
assert 2 <= N <= 12
HIGH = "SVI_v2_PRO_Wan2.2-I2V-A14B_HIGH_lora_rank_128_fp16.safetensors"
LOW = "SVI_v2_PRO_Wan2.2-I2V-A14B_LOW_lora_rank_128_fp16.safetensors"
# Measured (probe render, 33-frame segments): the first 5 frames of a new segment replay the last 5 frames of
# the previous one (frame 0 is not the anchor image), so they are cross-faded over them.
DROP, OVERLAP = 0, 5

d = json.load(open(src, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
assert not any(n["type"] == "DaSiWa_SeamlessLoop" for n in sg["nodes"]), "start from an I2V workflow"
assert not any(n["type"] in ("WanImageToVideoSVIPro", "MinesSVIProEndFrame") for n in sg["nodes"]), "already a Long workflow"
assert "end_image" in [i["name"] for i in sg["inputs"]], "start from an I2V workflow from workflows/ (it needs the end image input)"
T = {n.get("title"): n for n in sg["nodes"]}
L = {l["id"]: l for l in sg["links"]}

nid = iter(range(sg["state"]["lastNodeId"] + 1, sg["state"]["lastNodeId"] + 400))
lid = iter(range(sg["state"]["lastLinkId"] + 1, sg["state"]["lastLinkId"] + 2000))


def lk(o, os_, t, ts, typ):
    i = next(lid)
    sg["links"].append({"id": i, "origin_id": o, "origin_slot": os_, "target_id": t, "target_slot": ts, "type": typ})
    if o == -10:
        sg["inputs"][os_]["linkIds"].append(i)
    return i


def slot(node, name):
    return [k for k, i in enumerate(node["inputs"]) if i["name"] == name][0]


def src_of(node, name):
    l = L[node["inputs"][slot(node, name)]["link"]]
    return l["origin_id"], l["origin_slot"]


def pin(name, typ, widget=False, optional=False):
    p = {"localized_name": name, "name": name, "type": typ, "link": None}
    if optional:
        p["shape"] = 7
    if widget:
        p["widget"] = {"name": name}
    return p


def out(name, typ):
    return {"localized_name": name, "name": name, "type": typ, "links": None}


def node(typ, title, pos, size, inputs, outputs, widgets, cnr="comfy-core"):
    n = {"id": next(nid), "type": typ, "title": title, "pos": pos, "size": size, "flags": {}, "order": 60, "mode": 0,
         "inputs": inputs, "outputs": outputs, "properties": {"Node name for S&R": typ, "cnr_id": cnr}}
    if widgets is not None:
        n["widgets_values"] = list(widgets.values())
        n["widgets_values_named"] = dict(widgets)
    sg["nodes"].append(n)
    return n


def retarget(old_o, old_slot, new_o, new_slot, only_to=None):
    for l in sg["links"]:
        if l["origin_id"] == old_o and l["origin_slot"] == old_slot and (only_to is None or l["target_id"] in only_to):
            l["origin_id"], l["origin_slot"] = new_o, new_slot


def drop_node(n):
    sg["nodes"].remove(n)
    gone = {l["id"] for l in sg["links"] if n["id"] in (l["origin_id"], l["target_id"])}
    sg["links"][:] = [l for l in sg["links"] if l["id"] not in gone]
    for i in sg["inputs"]:
        i["linkIds"] = [x for x in i["linkIds"] if x not in gone]


hi_load, lo_load = T["Load high-noise model"], T["Load low-noise model"]
hi_s, lo_s = T["Sample high-noise steps"], T["Sample low-noise steps"]
enc, neg, clip_ld, vae = T["Encode prompt"], T["Encode negative prompt"], T["Load text encoder"], T["Load VAE"]
scale, size, old_lat, dec = T["Scale image to megapixels"], T["Get image width and height"], \
    T["Build latent from start and end image"], T["Decode latent to frames"]
cm = T["Fix color drift"]
frames = src_of(old_lat, "length")

# 0. colour: per-frame match to the start image instead of the I2V drift fix. Long clips fade in contrast and
#    color segment by segment on the moving figure, which the drift fix (fitted on still areas) does not catch:
#    4 segments, last frame contrast 75% with the drift fix, 94% with per-frame 0.75. Same slots 0 and 2.
cm.update(type="ColorTransfer", title="Match colors to start image",
          properties={"Node name for S&R": "ColorTransfer", "cnr_id": "comfy-core"},
          widgets_values=["reinhard_lab", "per_frame", 0.75])
cm.pop("widgets_values_named", None)
cm["inputs"] = [pin("image_target", "IMAGE"), pin("image_ref", "IMAGE"), pin("strength", "FLOAT", True)]
cm["outputs"][0]["name"] = cm["outputs"][0]["localized_name"] = "image"
sg["links"][:] = [l for l in sg["links"] if not (l["target_id"] == cm["id"] and l["target_slot"] == 1)]
lk(scale["id"], 0, cm["id"], 1, "IMAGE")

# 1. SVI LoRAs right after the model loaders
for ld, lora, x in ((hi_load, HIGH, "high"), (lo_load, LOW, "low")):
    n = node("LoraLoaderModelOnly", f"Apply SVI LoRA ({x})", [ld["pos"][0] + 410, ld["pos"][1] + 1240], [380, 110],
             [pin("model", "MODEL"), pin("lora_name", "COMBO", True), pin("strength_model", "FLOAT", True)],
             [out("MODEL", "MODEL")], {"lora_name": lora, "strength_model": 1.0})
    retarget(ld["id"], 0, n["id"], 0)
    lk(ld["id"], 0, n["id"], 0, "MODEL")

# 2. anchor = the scaled start image as a latent
anchor = node("VAEEncode", "Encode start image (anchor)", [870, 1300], [380, 100],
              [pin("pixels", "IMAGE"), pin("vae", "VAE")], [out("LATENT", "LATENT")], None)
lk(scale["id"], 0, anchor["id"], 0, "IMAGE")
lk(vae["id"], 0, anchor["id"], 1, "VAE")


def svi(title, pos, pos_cond, prev):
    n = node("MinesSVIProEndFrame", title, pos, [380, 240],
             [pin("positive", "CONDITIONING"), pin("negative", "CONDITIONING"), pin("vae", "VAE"),
              pin("length", "INT", True), pin("anchor_samples", "LATENT"), pin("motion_latent_count", "INT", True),
              pin("prev_samples", "LATENT", optional=True), pin("end_image", "IMAGE", optional=True)],
             [out("positive", "CONDITIONING"), out("negative", "CONDITIONING"), out("latent", "LATENT")],
             {"length": 81, "motion_latent_count": 1})
    n["properties"].pop("cnr_id")
    n["properties"]["aux_id"] = "kuromatcha/mines-pack"
    lk(*pos_cond, n["id"], 0, "CONDITIONING")
    lk(neg["id"], 0, n["id"], 1, "CONDITIONING")
    lk(vae["id"], 0, n["id"], 2, "VAE")
    lk(*frames, n["id"], 3, "INT")
    lk(anchor["id"], 0, n["id"], 4, "LATENT")
    if prev:
        lk(prev, 0, n["id"], 6, "LATENT")
    return n


def add_input(at, entry):
    """Insert a subgraph input at slot `at`, moving the links of later inputs along."""
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["origin_slot"] >= at:
            l["origin_slot"] += 1
    sg["inputs"].insert(at, entry)


# 3. segment 1 replaces the plain I2V latent
s1 = svi("Build segment 1 latent (SVI)", old_lat["pos"], (enc["id"], 0), None)
for k in range(3):
    retarget(old_lat["id"], k, s1["id"], k)
drop_node(old_lat)
end_slot = [i["name"] for i in sg["inputs"]].index("end_image")
lk(-10, end_slot, s1["id"], 7, "IMAGE")
if not any(l["origin_id"] == size["id"] for l in sg["links"]):
    drop_node(size)
hi_s["title"], lo_s["title"] = "Sample high-noise steps (segment 1)", "Sample low-noise steps (segment 1)"
enc["title"], dec["title"] = "Encode prompt 1", "Decode segment 1"
retarget(dec["id"], 0, -1, -1, only_to={cm["id"]})   # color drift fix is re-fed from the joined frames below

# 4. segments 2..N
text_slot = [i["name"] for i in sg["inputs"]].index("text")
joined, prev_low = (dec["id"], 0), lo_s["id"]
for k in range(2, N + 1):
    x0, y0 = 4600 + (k - 2) * 430, 0
    name = f"text_{k + 8}"  # text_1 is the negative prompt; keep clear of ComfyUI's own suffixes
    sg["inputs"].insert(text_slot + k - 1, {"id": str(uuid.uuid4()), "name": name, "type": "STRING", "linkIds": [],
                                            "label": f"prompt {k}", "pos": [0, 0]})
    for l in sg["links"]:
        if l["origin_id"] == -10 and l["origin_slot"] >= text_slot + k - 1 and l["id"] not in sg["inputs"][text_slot + k - 1]["linkIds"]:
            l["origin_slot"] += 1
    e = node("CLIPTextEncode", f"Encode prompt {k}", [x0, y0], [400, 200],
             [pin("clip", "CLIP"), pin("text", "STRING", True)], [out("CONDITIONING", "CONDITIONING")], {"text": ""})
    lk(clip_ld["id"], 0, e["id"], 0, "CLIP")
    lk(-10, text_slot + k - 1, e["id"], 1, "STRING")
    s = svi(f"Build segment {k} latent (SVI)", [x0, y0 + 250], (e["id"], 0), prev_low)
    ename = f"end_image_{k + 8}"
    add_input(end_slot + k - 1, {"id": str(uuid.uuid4()), "name": ename, "type": "IMAGE", "linkIds": [],
                                 "localized_name": ename, "label": f"end image {k}", "shape": 7, "pos": [0, 0]})
    lk(-10, end_slot + k - 1, s["id"], 7, "IMAGE")
    text_slot += 1  # the end image input went in before the prompts
    samplers = []
    for base, first in ((hi_s, True), (lo_s, False)):
        n = copy.deepcopy(base)
        n["id"] = next(nid)
        n["title"] = base["title"].replace("(segment 1)", f"(segment {k})")
        n["pos"] = [x0, y0 + (500 if first else 1080)]
        n["flags"] = {}
        if first:  # its own seed, so segments do not share noise
            n["widgets_values"][1] = (n["widgets_values"][1] * 31 + k * 7919) % (2 ** 48)
            if "noise_seed" in n.get("widgets_values_named", {}):
                n["widgets_values_named"]["noise_seed"] = n["widgets_values"][1]
        for i in n["inputs"]:
            i["link"] = None
        for o in n["outputs"]:
            o["links"] = None
        sg["nodes"].append(n)
        for nm in ("model", "steps", "cfg", "end_at_step" if first else "start_at_step"):
            if base["inputs"][slot(base, nm)]["link"] is not None:
                lk(*src_of(base, nm), n["id"], slot(n, nm), base["inputs"][slot(base, nm)]["type"])
        lk(s["id"], 0, n["id"], slot(n, "positive"), "CONDITIONING")
        lk(s["id"], 1, n["id"], slot(n, "negative"), "CONDITIONING")
        lk(s["id"] if first else samplers[0]["id"], 2 if first else 0, n["id"], slot(n, "latent_image"), "LATENT")
        samplers.append(n)
    dk = node("VAEDecode", f"Decode segment {k}", [x0, y0 + 1660], [400, 100],
              [pin("samples", "LATENT"), pin("vae", "VAE")], [out("IMAGE", "IMAGE")], None)
    lk(samplers[1]["id"], 0, dk["id"], 0, "LATENT")
    lk(vae["id"], 0, dk["id"], 1, "VAE")
    new = dk
    if DROP:
        new = node("ImageFromBatch", f"Drop first frames (segment {k})", [x0, y0 + 1810], [400, 130],
                   [pin("image", "IMAGE"), pin("batch_index", "INT", True), pin("length", "INT", True)],
                   [out("IMAGE", "IMAGE")], {"batch_index": DROP, "length": 4096})
        lk(dk["id"], 0, new["id"], 0, "IMAGE")
    jn = node("ImageBatchExtendWithOverlap", f"Join segment {k}", [x0, y0 + 1990], [400, 180],
              [pin("source_images", "IMAGE"), pin("overlap", "INT", True), pin("overlap_side", "COMBO", True),
               pin("overlap_mode", "COMBO", True), pin("new_images", "IMAGE", optional=True)],
              [out("source_images", "IMAGE"), out("start_images", "IMAGE"), out("extended_images", "IMAGE")],
              {"overlap": OVERLAP, "overlap_side": "source", "overlap_mode": "linear_blend"}, cnr="comfyui-kjnodes")
    lk(*joined, jn["id"], 0, "IMAGE")
    lk(new["id"], 0, jn["id"], 4, "IMAGE")
    joined, prev_low = (jn["id"], 2), samplers[1]["id"]
    sg["groups"].append({"id": sg["state"]["lastGroupId"] + k - 1, "title": f"Segment {k}",
                         "bounding": [x0 - 20, -76, 440, 2290], "color": "#3f789e", "font_size": 24, "flags": {}})
sg["state"]["lastGroupId"] += N - 1
lk(*joined, cm["id"], slot(cm, "image_target"), "IMAGE")
sg["links"][:] = [l for l in sg["links"] if l["origin_id"] != -1]

# 5. front panel: prompt k inputs after prompt 1, labels
wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
vals = dict(zip(wn, outer["widgets_values"]))
at = [i["name"] for i in outer["inputs"]].index("text") + 1
for k in range(2, N + 1):
    name = f"text_{k + 8}"
    outer["inputs"].insert(at + k - 2, {"label": f"prompt {k}", "name": name, "type": "STRING",
                                        "widget": {"name": name}, "link": None})
    vals[name] = ""
loader = [n for n in d["nodes"] if n["type"] == "LoadImage" and n.get("title", "").startswith("End image")][0]
loader["title"] = "End image (segment 1)"
ox = max(n["pos"][0] + n["size"][0] for n in d["nodes"]) + 40
for k in range(2, N + 1):
    ename = f"end_image_{k + 8}"
    d["last_node_id"] += 1
    d["last_link_id"] += 1
    ld = copy.deepcopy(loader)
    ld["id"], ld["title"] = d["last_node_id"], f"End image (segment {k})"
    ld["pos"] = [ox + (k - 2) * (loader["size"][0] + 40), loader["pos"][1]]
    ld["outputs"][0]["links"] = [d["last_link_id"]]
    d["nodes"].append(ld)
    outer["inputs"].insert([i["name"] for i in outer["inputs"]].index("end_image") + k - 1,
                           {"localized_name": ename, "label": f"end image {k}", "name": ename, "type": "IMAGE",
                            "shape": 7, "link": d["last_link_id"]})
    d["links"].append([d["last_link_id"], ld["id"], 0, outer["id"], 0, "IMAGE"])
for s_, i in enumerate(outer["inputs"]):
    for l in d["links"]:
        if l[3] == outer["id"] and l[0] == i.get("link"):
            l[4] = s_
for i in sg["inputs"] + outer["inputs"]:
    if i["name"] == "end_image":
        i["label"] = "end image 1"
    if i["name"] == "text":
        i["label"] = "prompt 1"
    if i["name"] == "value_1":
        i["label"] = "segment length (seconds)"
    if i["name"] == "strength":
        i["label"] = "color match strength"
assert [i["name"] for i in outer["inputs"]] == [i["name"] for i in sg["inputs"]]
wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
P1 = ("A woman with black hair in a messy bun, seen from behind in a wet light blue dress and a beige knit cardigan, "
      "looks back over her shoulder with a soft closed-mouth smile. She sways her hips slowly from side to side, her "
      "shoulders rocking gently, her lips staying closed and still. The camera holds still on a locked-off full body "
      "shot at eye level. Plain white background, soft studio lighting, anime illustration.")
P2 = ("The woman slowly turns around to face the viewer, her cardigan sleeves swinging, then raises one hand and "
      "waves gently while smiling with her lips closed. The camera holds still on a locked-off full body shot at eye "
      "level. Plain white background, soft studio lighting, anime illustration.")
vals["text"] = P1
vals["strength"] = 0.75  # colour match: measured 25% contrast loss over 4 segments without it
for k in range(2, N + 1):
    vals[f"text_{k + 8}"] = P2 if k == 2 else ""
outer["widgets_values"] = [vals[n] for n in wn]
outer["widgets_values_named"] = {n: vals[n] for n in wn}

# 6. identity: new subgraph id, names, save prefix, guide
new_id = str(uuid.uuid4())
sg["id"] = outer["type"] = new_id
sg["name"] = "Mine's Long NVFP4"
d["id"] = str(uuid.uuid4())
for n in d["nodes"]:
    if n["type"] == "SaveVideo":
        n["widgets_values"][0] = "video/clip"
        if "widgets_values_named" in n:
            n["widgets_values_named"][list(n["widgets_values_named"])[0]] = n["widgets_values"][0]
note = [n for n in d["nodes"] if n["type"] == "MarkdownNote"][0]
g = note["widgets_values"][0]
for a, b in (("- **color drift fix**: 1 · 0 = off. Removes slow color drift so later frames keep the colors of the first frame; motion and flashes are left alone.\n",
              "- **color match strength**: 0 off · 0.75 on\n"),
             ("## Prompt\n",f"## Prompts\n- One prompt per 5-second segment, {N} segments. The next motion starts where the last one ended.\n"),
             ("- Same start and end pose: use the Loop workflow.\n", "- Each prompt: describe only that segment's motion; repeat camera and scene.\n"),
             ("- **duration (seconds)**: 5. Longer drifts.\n", "- **segment length (seconds)**: 5. Longer drifts.\n"),
             ("- Seed: random. To keep one: *Sample high-noise steps* → fixed.\n",
              "- Seeds: random. To keep one: *Sample high-noise steps (segment N)* → fixed.\n- SVI LoRA strength: *Apply SVI LoRA* nodes (1.0).\n"),
             (END_LINE, "- **End image (segment N)** (optional): the pose that segment ends on. Bypassed (Ctrl+B) = it ends "
                        "freely and the next segment continues from there. Keep framing, background and style the same.\n"),
             ("1. Test: 0.3 MP, 3 s, extras off.\n", "1. Test: 0.3 MP, 3 s segments, extras off.\n")):
    assert g.count(a) == 1, a
    g = g.replace(a, b)
note["widgets_values"][0] = g

# 7. bookkeeping and checks
for n in sg["nodes"]:
    for k, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == k]
        assert len(hit) <= 1, (n["id"], i["name"])
        i["link"] = hit[0] if hit else None
    for k, o in enumerate(n.get("outputs", [])):
        hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == k]
        o["links"] = hit or None
for s_, i in enumerate(sg["inputs"]):
    i["linkIds"] = [l["id"] for l in sg["links"] if l["origin_id"] == -10 and l["origin_slot"] == s_]
    assert i["linkIds"], i["name"]
sg["state"]["lastNodeId"] = max(n["id"] for n in sg["nodes"])
sg["state"]["lastLinkId"] = max(l["id"] for l in sg["links"])
ids = {n["id"] for n in sg["nodes"]} | {-10, -20}
assert all(l["origin_id"] in ids and l["target_id"] in ids for l in sg["links"])
for n in sg["nodes"]:
    if n["type"] in ("KSamplerAdvanced", "MinesSVIProEndFrame", "VAEDecode", "ImageBatchExtendWithOverlap"):
        assert all(i["link"] is not None for i in n["inputs"] if i.get("shape") != 7 and not i.get("widget")), n["title"]
open(dst, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print(f"long workflow ({N} segments):", dst.replace("\\", "/").split("/")[-1])
