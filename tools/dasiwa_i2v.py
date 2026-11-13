"""Non-loop image-to-video from a DaSiWa loop workflow, using the developer's I2V engine (C-AiO-95):
start image -> WanImageToVideo (no end frame). No Seamless Loop (developer default off).
Color match kept but at the developer default (off -> strength 0). Everything else unchanged.
"""
import json, sys, uuid

src, dst, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(src, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
nodes = {n["id"]: n for n in sg["nodes"]}

old_id, new_id = sg["id"], str(uuid.uuid4())
d["id"] = str(uuid.uuid4())
sg["id"] = new_id
sg["name"] = sg["name"].replace("Loop Video", "Image to Video").replace(" FLF", "")
outer["type"] = new_id

# 1) first/last-frame latent -> image-to-video latent (same links, mapped by input name)
f = nodes[98]
links_by_name = {i["name"]: i["link"] for i in f["inputs"]}
names = ["positive", "negative", "vae", "clip_vision_output", "start_image", "ref_pad_image", "width", "height", "length", "batch_size"]
types = ["CONDITIONING", "CONDITIONING", "VAE", "CLIP_VISION_OUTPUT", "IMAGE", "IMAGE", "INT", "INT", "INT", "INT"]
optional = {"clip_vision_output", "start_image", "ref_pad_image"}
widgets = {"width", "height", "length", "batch_size"}
end_link = links_by_name.get("end_image")
f["type"] = "WanImageToVideo"
f["title"] = "Start frame -> latent (image to video)"
f["properties"] = {"Node name for S&R": "WanImageToVideo", "cnr_id": "comfy-core"}
f["inputs"] = []
for nm, ty in zip(names, types):
    i = {"localized_name": nm, "name": nm, "type": ty, "link": links_by_name.get(nm)}
    if nm in optional:
        i["shape"] = 7
    if nm in widgets:
        i["widget"] = {"name": nm}
    f["inputs"].append(i)
sg["links"] = [l for l in sg["links"] if l["id"] != end_link]
for l in sg["links"]:  # re-number target slots into the new input order
    if l["target_id"] == 98:
        l["target_slot"] = [i["link"] for i in f["inputs"]].index(l["id"])

# 2) drop Seamless Loop: color match feeds upscale + switch directly
sg["nodes"] = [n for n in sg["nodes"] if n["type"] != "DaSiWa_SeamlessLoop"]
loop_id = 172
for l in sg["links"]:
    if l["origin_id"] == loop_id:
        l["origin_id"], l["origin_slot"] = 171, 0
sg["links"] = [l for l in sg["links"] if l["target_id"] != loop_id]
nodes = {n["id"]: n for n in sg["nodes"]}
nodes[171]["title"] = "Color match to start image (dev default off: strength 0; try 0.75 if colors drift)"
for g in sg["groups"]:
    if g["title"].startswith("7 ·"):
        g["title"] = "7 · Output (color match -> optional upscale -> interpolation)"
    if g["title"].startswith("2 ·"):
        g["title"] = "2 · Prompts & start frame"

# 3) outside values: color match off (developer default), loop wording out of the prompt, own output name
wn = [i["name"] for i in outer["inputs"] if i.get("widget")]
vals = dict(zip(wn, outer["widgets_values"]))
vals["strength"] = 0.0
vals["text"] = vals["text"].replace(" The motion is a smooth repeating cycle that ends in the same pose it started in.", "")
outer["widgets_values"] = [vals[n] for n in wn]
outer["widgets_values_named"] = dict(zip(wn, outer["widgets_values"]))
for n in d["nodes"]:
    if n["type"] == "SaveVideo":
        n["widgets_values"][0] = prefix
        if "widgets_values_named" in n:
            n["widgets_values_named"]["filename_prefix"] = prefix

# rebuild link fields + checks
lids = {l["id"] for l in sg["links"]}
for n in sg["nodes"]:
    for k, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == k]
        i["link"] = hit[0] if hit else None
    for k, o in enumerate(n.get("outputs", [])):
        hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == k]
        o["links"] = hit or None
for i in sg["inputs"]:
    i["linkIds"] = [x for x in i["linkIds"] if x in lids]
allids = {n["id"] for n in sg["nodes"]} | {-10, -20}
assert all(l["origin_id"] in allids and l["target_id"] in allids for l in sg["links"])
out = json.dumps(d, ensure_ascii=False)
assert old_id not in out and "SeamlessLoop" not in out and "FirstLastFrame" not in out
open(dst, "w", encoding="utf-8").write(out)
print("wrote", dst.split("/")[-1])
