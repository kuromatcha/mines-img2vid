# Troubleshooting

| Problem | Fix |
|---|---|
| *Allocation on device 0 would exceed allowed memory* during sampling | Video memory too small for that size. Turn **FFN chunking** on, or lower megapixels. **Restart ComfyUI after any out-of-memory error** (a run right after one produced broken NaN frames). |
| *Seamless Loop input contains NaN or infinity* | Broken frames, usually right after an out-of-memory error. Restart ComfyUI and run again. If it repeats in a fresh session, remove `--fast fp16_accumulation`. |
| Crash: *Windows fatal exception: access violation* while loading a model | Out of memory. Restart ComfyUI before rendering, enlarge the page file, don't use `--disable-dynamic-vram`. |
| Loop "flashes" white at the loop point | Keep **color match** on (0.75) and the **Seamless Loop** node active; keep duration at 5 s (16 fps). |
| Mouth keeps moving | Prompt for closed, still lips; turn NAG on (inside the subgraph: both *Switch: NAG* nodes). |
| Red "missing node" boxes | Install the custom node pack from the [install guide](install.md) and restart. |
| NVFP4 workflow errors or is slow | Needs an RTX 50-series GPU and PyTorch built for CUDA 13; otherwise use the GGUF workflows. |
| Model files missing in dropdowns | Check the folders in the [install guide](install.md), then press **R** in ComfyUI or restart it. |
