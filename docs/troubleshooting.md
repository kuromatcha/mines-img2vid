# Troubleshooting

| Problem | Fix |
|---|---|
| *Allocation on device 0 would exceed allowed memory* during sampling | Video memory too small for that size. Turn **FFN chunking** on, or lower megapixels. **Restart ComfyUI after any out-of-memory error** (a run right after one produced broken NaN frames). |
| *Seamless Loop input contains NaN or infinity* | Broken frames, usually right after an out-of-memory error. Restart ComfyUI and run again. If it repeats in a fresh session, remove `--fast fp16_accumulation`. |
| Crash: *Windows fatal exception: access violation* while loading a model | Out of memory. Restart ComfyUI before rendering, enlarge the page file, don't use `--disable-dynamic-vram`. |
| Loop "flashes" white at the loop point | Keep **color match** on (0.75) and the **Seamless Loop** node active; keep duration at 5 s (16 fps). |
| GGUF workflow fails with *cutlass_fp16_linear: K mismatch* | ComfyUI 0.45.3 (core update of 2026-11-12) runs Wan's feed-forward through an fp16-accumulation kernel that GGUF weights don't support. The GGUF workflows include a *Turn off fp16 accumulation (GGUF fix)* node for each model (KJNodes). If you build your own GGUF workflow, add *Model Patch Torch Settings* with fp16 accumulation off after the GGUF loader, or remove `--fast fp16_accumulation`. |
| Mouth keeps moving | Prompt for closed, still lips; turn **negative** on. If it still moves, also turn on *Switch: NAG (low)* inside the subgraph. |
| The clip cross-fades or morphs into the end image | The end image is too different from the start image (framing, size in frame, background, outfit or style), or the prompt does not describe the motion between the two poses. Use an end image from the same character sheet or render, and describe the move in the prompt. Set **end image** to *none* to turn it off. |
| Red "missing node" boxes | Install the custom node pack from the [install guide](install.md) and restart. |
| NVFP4 workflow errors or is slow | Needs an RTX 50-series GPU and PyTorch built for CUDA 13; otherwise use the GGUF workflows. |
| Model files missing in dropdowns | Check the folders in the [install guide](install.md), then press **R** in ComfyUI or restart it. |
