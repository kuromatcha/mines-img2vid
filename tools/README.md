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

Run with ComfyUI's Python, e.g. `python -I tools/dasiwa_tidy.py "workflows/DaSiWa Loop GGUF.json"`. Back up the workflow first.
