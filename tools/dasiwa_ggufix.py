"""GGUF workflows: turn fp16 accumulation off for the GGUF models.

Since the ComfyUI core update of 2026-11-12 (0.45.3), Wan's feed-forward runs through a fused fp16-accumulation
GEMM when `--fast fp16_accumulation` is on. ComfyUI-GGUF weights reach it still packed, so sampling fails with
"cutlass_fp16_linear: K mismatch". KJNodes' Model Patch Torch Settings switches fp16 accumulation off right
before the GGUF model runs. Note: it does not switch it back on, so NVFP4 runs later in the same session run
without fp16 accumulation until ComfyUI restarts (slightly slower, same result).
Safe to run again.
"""
import json, sys

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
sg = d["definitions"]["subgraphs"][0]
loaders = [n for n in sg["nodes"] if n["type"] == "UnetLoaderGGUF"]
assert loaders, "not a GGUF workflow"
done = {l["origin_id"] for l in sg["links"]
        if l["target_id"] in {n["id"] for n in sg["nodes"] if n["type"] == "ModelPatchTorchSettings"}}
nid = max(n["id"] for n in sg["nodes"])
lid = max(l["id"] for l in sg["links"])
added = 0
for ld in loaders:
    if ld["id"] in done:
        continue
    nid += 1
    lid += 1
    x = "high" if "high" in (ld.get("title") or "").lower() else "low"
    sg["nodes"].append({
        "id": nid, "type": "ModelPatchTorchSettings", "title": f"Turn off fp16 accumulation ({x}, GGUF fix)",
        "pos": [ld["pos"][0], ld["pos"][1] + 1500 + (0 if x == "high" else 130)], "size": [380, 110],
        "flags": {}, "order": 70, "mode": 0,
        "inputs": [{"localized_name": "model", "name": "model", "type": "MODEL", "link": None},
                   {"localized_name": "enable_fp16_accumulation", "name": "enable_fp16_accumulation", "type": "BOOLEAN",
                    "widget": {"name": "enable_fp16_accumulation"}, "link": None}],
        "outputs": [{"localized_name": "MODEL", "name": "MODEL", "type": "MODEL", "links": None}],
        "properties": {"Node name for S&R": "ModelPatchTorchSettings", "cnr_id": "comfyui-kjnodes"},
        "widgets_values": [False], "widgets_values_named": {"enable_fp16_accumulation": False}})
    for l in sg["links"]:
        if l["origin_id"] == ld["id"]:
            l["origin_id"], l["origin_slot"] = nid, 0
    sg["links"].append({"id": lid, "origin_id": ld["id"], "origin_slot": 0, "target_id": nid, "target_slot": 0, "type": "MODEL"})
    added += 1
for n in sg["nodes"]:
    for k, i in enumerate(n["inputs"]):
        hit = [l["id"] for l in sg["links"] if l["target_id"] == n["id"] and l["target_slot"] == k]
        assert len(hit) <= 1
        i["link"] = hit[0] if hit else None
    for k, o in enumerate(n.get("outputs", [])):
        hit = [l["id"] for l in sg["links"] if l["origin_id"] == n["id"] and l["origin_slot"] == k]
        o["links"] = hit or None
sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], nid)
sg["state"]["lastLinkId"] = max(sg["state"]["lastLinkId"], lid)
open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
print(f"GGUF fix: {added} model(s) patched:", path.replace("\\", "/").split("/")[-1])
