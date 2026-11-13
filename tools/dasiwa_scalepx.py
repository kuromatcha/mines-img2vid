"""Replace tier preset + pad/crop sizing with core Scale Image to Total Pixels (lanczos, 16-px steps) + Get Image Size.

start image -> ImageScaleToTotalPixels(megapixels from outside, lanczos, steps 16) -> first/last frame
                                    -> GetImageSize -> latent width/height
decode -> color match directly (no crop-back needed). Color match ref = the scaled start image.
"""
import json, sys, uuid

path, default_mp = sys.argv[1], float(sys.argv[2])
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
outer = [n for n in d["nodes"] if n["type"] == sg["id"]][0]
REMOVE = {180, 181, 182, 183, 184, 185}
assert REMOVE & {n["id"] for n in sg["nodes"]}, "pad/crop sizing not found"

sg["nodes"] = [n for n in sg["nodes"] if n["id"] not in REMOVE]
sg["links"] = [l for l in sg["links"] if l["origin_id"] not in REMOVE and l["target_id"] not in REMOVE
               and not (l["target_id"] == 171 and l["target_slot"] == 1)]
nodes = {n["id"]: n for n in sg["nodes"]}
names = [i["name"] for i in sg["inputs"]]
img_slot, tier_slot = names.index("start_image"), names.index("resolution_preset")

SC, GS = 186, 187
core = lambda t: {"Node name for S&R": t, "cnr_id": "comfy-core"}
sg["nodes"] += [
    {"id": SC, "type": "ImageScaleToTotalPixels", "title": "Scale start image to megapixels (keeps shape, lanczos, 16-px steps)",
     "pos": [1080, 640], "size": [400, 200], "flags": {}, "order": 37, "mode": 0,
     "inputs": [{"localized_name": "image", "name": "image", "type": "IMAGE", "link": None},
                {"localized_name": "megapixels", "name": "megapixels", "type": "FLOAT", "widget": {"name": "megapixels"}, "link": None}],
     "outputs": [{"localized_name": "IMAGE", "name": "IMAGE", "type": "IMAGE", "links": None}],
     "properties": core("ImageScaleToTotalPixels"),
     "widgets_values": ["lanczos", default_mp, 16],
     "widgets_values_named": {"upscale_method": "lanczos", "megapixels": default_mp, "resolution_steps": 16}},
    {"id": GS, "type": "GetImageSize", "title": "Video size = scaled image size", "pos": [1080, 900], "size": [400, 120],
     "flags": {}, "order": 38, "mode": 0,
     "inputs": [{"localized_name": "image", "name": "image", "type": "IMAGE", "link": None}],
     "outputs": [{"localized_name": "width", "name": "width", "type": "INT", "links": None},
                 {"localized_name": "height", "name": "height", "type": "INT", "links": None},
                 {"localized_name": "batch_size", "name": "batch_size", "type": "INT", "links": None}],
     "properties": core("GetImageSize")},
]
nodes = {n["id"]: n for n in sg["nodes"]}

nl = max(l["id"] for l in sg["links"]) + 1
it = iter(range(nl, nl + 40))


def lk(o, os_, t, ts, typ):
    lid = next(it)
    sg["links"].append({"id": lid, "origin_id": o, "origin_slot": os_, "target_id": t, "target_slot": ts, "type": typ})
    return lid


s98 = {i["name"]: k for k, i in enumerate(nodes[98]["inputs"])}
img_link = lk(-10, img_slot, SC, 0, "IMAGE")
lk(SC, 0, GS, 0, "IMAGE")
lk(SC, 0, 98, s98["start_image"], "IMAGE")
lk(SC, 0, 98, s98["end_image"], "IMAGE")
lk(GS, 0, 98, s98["width"], "INT")
lk(GS, 1, 98, s98["height"], "INT")
lk(SC, 0, 171, 1, "IMAGE")
lk(87, 0, 171, 0, "IMAGE")

# outside: quality tier combo -> megapixels number
mp_in = sg["inputs"][tier_slot]
mp_in.update(name="megapixels", type="FLOAT", label="quality in megapixels (0.3 smoke test / 0.6 baseline / 0.8 HD)", linkIds=[])
mp_in["linkIds"].append(lk(-10, tier_slot, SC, 1, "FLOAT"))
sg["inputs"][img_slot]["linkIds"].append(img_link)

wnames = [i["name"] for i in outer["inputs"] if i.get("widget")]
vals = dict(zip(wnames, outer["widgets_values"]))
vals["megapixels"] = default_mp
for i in outer["inputs"]:
    if i["name"] == "resolution_preset":
        i.update(name="megapixels", type="FLOAT", widget={"name": "megapixels"}, label=mp_in["label"])
wnames = [i["name"] for i in outer["inputs"] if i.get("widget")]
outer["widgets_values"] = [vals[n] for n in wnames]
outer["widgets_values_named"] = dict(zip(wnames, outer["widgets_values"]))

for nid, y in ((171, 160), (172, 400)):
    nodes[nid]["pos"] = [2880, y]
for g in sg["groups"]:
    if g["title"].startswith("3 ·"):
        g["title"] = "3 · Size (megapixels, keeps shape), length & FPS"
        g["bounding"][3] = 1420
    if g["title"].startswith("7 ·"):
        g["title"] = "7 · Output (color match -> seamless loop -> optional upscale -> interpolation)"

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
sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], GS)
sg["state"]["lastLinkId"] = max(lids)

allids = {n["id"] for n in sg["nodes"]} | {-10, -20}
assert all(l["origin_id"] in allids and l["target_id"] in allids for l in sg["links"])
for slot, i in enumerate(sg["inputs"]):
    for lid in i["linkIds"]:
        assert [l for l in sg["links"] if l["id"] == lid][0]["origin_slot"] == slot, i["name"]
assert len(wnames) == len(outer["widgets_values"]) == len(sg["inputs"]) - 1
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print("sizing switched to scale-to-pixels in", path)
