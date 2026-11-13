# Settings

Values in **bold** are the defaults in these workflows. "dev" means the DaSiWa developer's recommendation.

| Setting | Default | Suggestion |
|---|---|---|
| prompt | your text | Structure (dev): 1) setting and appearance, 2) actions and motion, 3) camera. |
| negative prompt | "talking, speaking, mouth moving…" | Only has an effect when **NAG is on** or **CFG > 1**. |
| quality in megapixels | **0.6** | **0.3** smoke test · **0.6** baseline · **0.8** HD (dev range 0.52–0.83). Keeps the image's shape, any ratio. |
| duration (seconds) | **5** | dev: **5 s at 16 fps** (or 3 s at 24 fps) is Wan 2.2's native length; longer clips drift and wash out. |
| fps | **16** | dev: 16, or 24 for faster motion. 12 looks choppy. |
| seed | — | Keep the seed when comparing settings. |
| steps total | **4** | dev: 4 (distilled model). Even numbers only. |
| high/low split step | **2** | dev: 2 (half of 4). |
| CFG | **1** | dev: 1–1.5. 1 = fastest and ignores the negative prompt. |
| NAG on/off | **off** | dev default off (uses a lot of VRAM). Turn on to make the negative prompt work at CFG 1, e.g. to stop mouth movement. |
| NAG scale | **11** | dev: 11. |
| FFN chunking | **off** | dev default off. Splits the model's feed-forward step to cut peak VRAM. **Turn on for 0.7 MP and above on 16 GB cards** (0.8 MP ran out of VRAM without it). Slightly slower; marked experimental. Chunk count (4) is set inside the subgraph. |
| shift | **5** | dev: 5 (valid 5–10). |
| sampler / scheduler | **euler / simple** | dev: euler/simple always works; uni_pc_bh2/simple or euler/linear_quadratic as alternatives. |
| color match strength | **0.75** loop · **0** I2V | dev: 0.75 when used. Keep it on for loops (stops the washed-out end and the flash at the loop point). |
| upscale with model | **off** | AnimeSharpV4 doubles each side. Slow; sharpens line art, can harden soft shading. |
| RTX upscale 2× | **off** | NVIDIA RTX Video Super Resolution doubles each side. Fast and mild. When on it is used *instead of* the upscale model. Needs `nvidia-vfx` (see [install](install.md)). Mode, quality and scale are inside the subgraph (*RTX upscale* node: VSR / Ultra / 2.0; try *High Bitrate* mode for a softer, cleaner result). |
| interpolation multiplier | **1 (off)** | 2 = double fps with RIFE (built-in ComfyUI node, `rife_v4.26`). At 1 the step is skipped entirely. Loops stay seamless when interpolated. Leave at 1 while testing. |

**Inside the subgraph (advanced):**

- *Scale to megapixels → resolution_steps*: **16** (closest to the image's shape) or **32** (the developer's Div32).
- *Attention backend* nodes (one per model): **comfy kitchen attention** (dev default, faster INT8 attention). Set to *pytorch attention* to turn off.
