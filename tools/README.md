# tools

One-off Python scripts that built the workflows in `../workflows` from the original Wan 2.2 loop workflow. They edit the workflow JSON directly and check the wiring after each change. They are kept as a record of how the graphs were made, not as a build system: they assume specific node IDs and are meant to run once, in this order.

| Order | Script | What it did |
|---|---|---|
| 1 | `dasiwa_devwiring.py` | Rewired the model chain to the DaSiWa developer's defaults (no speed-up LoRAs, 4 steps, split 2, CFG 1, shift 5). |
| 2 | `dasiwa_colormatch.py` | Added color match to the start image (reinhard_lab, per frame, 0.75). |
| 3 | `dasiwa_seamless.py` | Added the developer's Seamless Loop node. |
| 4 | `dasiwa_upscale.py` | Added the optional model upscale behind a lazy switch. |
| 5 | `dasiwa_nag.py` | Added optional NAG and the closed-mouth prompt fix. |
| 6 | `dasiwa_tiers.py` | Quality-tier sizing (later replaced by step 8). |
| 7 | `dasiwa_anyratio.py` | Pad and crop-back for exact ratios (later replaced by step 8). |
| 8 | `dasiwa_scalepx.py` | Current sizing: Scale Image to Total Pixels (lanczos, 16 px steps). |
| 9 | `dasiwa_i2v.py` | Made the non-loop I2V versions from the loop versions. |
| 10 | `dasiwa_chunk.py` | Added optional FFN chunking (KJNodes). |
| 11 | `dasiwa_tidy.py` | Layout clean-up: short names, grid, groups, setting order. |
| 12 | `dasiwa_coreinterp.py` | Interpolation with ComfyUI's built-in RIFE nodes (skipped at multiplier 1), interpolated loop point for loops, fps default 16. |
| 13 | `dasiwa_rtx.py` | Added the optional RTX Video Super Resolution upscale behind a lazy switch (used instead of the model upscale). |
| 14 | `dasiwa_guide.py` | Plain setting names, literal node titles, one Guide note with all the advice; sampling settings (steps, split step, seed, cfg, shift, sampler, scheduler, NAG scale) and the model pickers moved off the front panel; NAG on/off stays as **negative**, driving only the high-noise NAG; toggle order FFN chunking, negative, model upscale, RTX upscale. |
| 15 | `dasiwa_long.py` | Made the Long workflows from the finished I2V ones: SVI 2.0 Pro LoRAs, N chained segments with one prompt each, joined with a short cross-fade; an optional end image per segment (needs step 17 first). `python -I tools/dasiwa_long.py <I2V workflow> <Long workflow> <segments>` |
| 16 | `dasiwa_ggufix.py` | GGUF workflows: *Model Patch Torch Settings* (KJNodes) turns fp16 accumulation off before each GGUF model runs. Fixes *cutlass_fp16_linear: K mismatch* after the ComfyUI 0.45.3 core update. Run it on the GGUF I2V/Loop workflows before `dasiwa_long.py`. |
| 17 | `dasiwa_endframe.py` | I2V workflows: optional end image. *Wan Image To Video* becomes *Wan First-Last-Frame to Video*, fed by a front-panel *Load Image (optional)* (`none` = skip). Run it on the I2V workflows before `dasiwa_long.py`, which then gives every segment its own optional end image through *Wan Image To Video SVIPro (end frame)* ([`custom_nodes/ComfyUI-DaSiWa-EndFrame`](../custom_nodes/ComfyUI-DaSiWa-EndFrame)). |
| 18 | `dasiwa_layout.py` | Layout pass for all workflows, run last: front-panel **shift** (drives both *Set shift* nodes); subgraph nodes placed by title into one group per stage (Models, Input, Timing, Sampling, High noise, Low noise, Segment N, Decode, Upscale, Interpolate, Video), each sized to its nodes; image loaders, settings, video and Guide in one row on the front, all 960 px tall on the 20 px snap grid (images and video 480 wide, settings 640, Guide 560). Fails if a node has no place. Safe to run again. |
| 19 | `dasiwa_tiledvae.py` | I2V and Loop workflows: optional tiled VAE decode. A front-panel **tiled VAE decode** toggle (default off, after FFN chunking) picks between *VAE Decode* and the built-in *VAE Decode (Tiled)* through a lazy switch. Run `dasiwa_layout.py` again afterwards to place the two new nodes. |

Run with ComfyUI's Python, e.g. `python -I tools/dasiwa_tidy.py "workflows/Mine's Loop GGUF.json"`. Back up the workflow first.
