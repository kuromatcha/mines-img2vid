"""I2V workflows: optional end frame.

Usage: python -I tools/dasiwa_endframe.py <I2V workflow>

- "Build latent from start image" (Wan Image To Video) becomes Wan First-Last-Frame to Video, which takes the start
  image and an optional end image. Without an end image it builds the same latent as Wan Image To Video.
- New front-panel node "End image (optional)" (Load Image (optional), ComfyUI-DaSiWa-EndFrame) feeds a new
  subgraph input "end image". At "none" it outputs nothing and the clip runs as plain I2V.
- The end image is resized and center-cropped to the start image's size by the node.
Run before dasiwa_long.py (the Long builder takes the end image over for segment 1). Safe to run again.
"""
import json, sys, uuid

END_LINE = ("- **End image** (optional): the pose the clip ends on, e.g. the front view after a turn. "
            "*none* = skip. Keep framing, background and style the same as the start image.\n")
path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
T = {n.get("title"): n for n in sg["nodes"]}
if "end_image" in [i["name"] for i in sg["inputs"]]:
    print("end frame: already there:", path.replace("\\", "/").split("/")[-1])
    sys.exit()
lat = T["Build latent from start image"]
assert lat["type"] == "WanImageToVideo", "start from an I2V workflow"

# 1. Wan Image To Video -> Wan First-Last-Frame to Video (same widgets: width, height, length, batch_size)
old = [i["name"] for i in lat["inputs"]]


def p(name, typ, widget=False, optional=False):
    q = {"localized_name": name, "name": name, "type": typ, "link": None}
    if optional:
        q["shape"] = 7
    if widget:
        q["widget"] = {"name": name}
    return q


lat["type"] = "WanFirstLastFrameToVideo"
lat["title"] = "Build latent from start and end image"
lat["properties"]["Node name for S&R"] = "WanFirstLastFrameToVideo"
lat["inputs"] = [p("positive", "CONDITIONING"), p("negative", "CONDITIONING"), p("vae", "VAE"),
                 p("clip_vision_start_image", "CLIP_VISION_OUTPUT", optional=True),
                 p("clip_vision_end_image", "CLIP_VISION_OUTPUT", optional=True),
                 p("start_image", "IMAGE", optional=True), p("end_image", "IMAGE", optional=True),
                 p("width", "INT", True), p("height", "INT", True), p("length", "INT", True), p("batch_size", "INT", True)]
new = [i["name"] for i in lat["inputs"]]
for l in sg["links"]:
    if l["target_id"] == lat["id"]:
        name = old[l["target_slot"]]
        assert name in new, name
        l["target_slot"] = new.index(name)

# 2. subgraph input "end image" right after the start image
sl = 1
for l in sg["links"]:
    if l["origin_id"] == -10 and l["origin_slot"] >= sl:
        l["origin_slot"] += 1
lid = sg["state"]["lastLinkId"] + 1
sg["inputs"].insert(sl, {"id": str(uuid.uuid4()), "name": "end_image", "type": "IMAGE", "linkIds": [lid],
                         "localized_name": "end_image", "label": "end image", "shape": 7, "pos": [0, 0]})
sg["links"].append({"id": lid, "origin_id": -10, "origin_slot": sl, "target_id": lat["id"],
                    "target_slot": new.index("end_image"), "type": "IMAGE"})
sg["state"]["lastLinkId"] = lid
for n in sg["nodes"]:
    for k, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == k]
        assert len(hit) <= 1, (n["title"], i["name"])
        i["link"] = hit[0] if hit else None
for s_, i in enumerate(sg["inputs"]):
    i["linkIds"] = [l["id"] for l in sg["links"] if l["origin_id"] == -10 and l["origin_slot"] == s_]
    assert i["linkIds"], i["name"]

# 3. front panel: "End image (optional)" under the start image
start = [n for n in d["nodes"] if n["type"] == "LoadImage"][0]
nid, olid = d["last_node_id"] + 1, d["last_link_id"] + 1
d["nodes"].append({
    "id": nid, "type": "DaSiWaLoadImageOptional", "title": "End image (optional)",
    "pos": [start["pos"][0], start["pos"][1] + start["size"][1] + 60], "size": list(start["size"]),
    "flags": {}, "order": 1, "mode": 0,
    "inputs": [{"localized_name": "image", "name": "image", "type": "COMBO", "widget": {"name": "image"}, "link": None},
               {"name": "upload", "type": "IMAGEUPLOAD", "widget": {"name": "upload"}, "link": None}],
    "outputs": [{"localized_name": "IMAGE", "name": "IMAGE", "type": "IMAGE", "links": [olid]},
                {"localized_name": "MASK", "name": "MASK", "type": "MASK", "links": None}],
    "properties": {"Node name for S&R": "DaSiWaLoadImageOptional", "aux_id": "kuromatcha/mines-img2vid"},
    "widgets_values": ["none", "image"]})
outer["inputs"].insert(sl, {"localized_name": "end_image", "label": "end image", "name": "end_image",
                            "type": "IMAGE", "shape": 7, "link": olid})
for l in d["links"]:
    if l[3] == outer["id"] and l[4] >= sl:
        l[4] += 1
d["links"].append([olid, nid, 0, outer["id"], sl, "IMAGE"])
d["last_node_id"], d["last_link_id"] = nid, olid
assert [i["name"] for i in outer["inputs"]] == [i["name"] for i in sg["inputs"]]

# 4. guide
note = [n for n in d["nodes"] if n["type"] == "MarkdownNote"][0]
a = "- Negative prompt works only with **negative** on.\n"
assert note["widgets_values"][0].count(a) == 1
note["widgets_values"][0] = note["widgets_values"][0].replace(a, END_LINE + a)
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("end frame added:", path.replace("\\", "/").split("/")[-1])
