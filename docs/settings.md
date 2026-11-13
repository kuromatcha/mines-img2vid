# Settings

Values in **bold** are the defaults in these workflows. The setting names match the front panel; the **Guide** note in each workflow has the short version of this page. "dev" means the DaSiWa developer's recommendation.

| Setting | Default | Suggestion |
|---|---|---|
| prompt | your text | Structure (dev): 1) subject, 2) motion, 3) camera, 4) scene. One paragraph, 80–120 words, most of them on motion. See [Recommended practice](practice.md). |
| negative prompt | "talking, speaking, mouth moving…" | Only has an effect when **negative** is on (or CFG is above 1, inside the subgraph). |
| negative | **off** | Turns on NAG, which makes the negative prompt work at CFG 1, e.g. to stop mouth movement. Dev default off; uses a lot of VRAM. |
| megapixels | **0.6** | **0.3** smoke test · **0.6** baseline · **0.8** HD (dev range 0.52–0.83). Keeps the image's shape, any ratio. |
| duration (seconds) | **5** | dev: **5 s at 16 fps** (or 3 s at 24 fps) is Wan 2.2's native length; longer clips drift and wash out. |
| fps | **16** | dev: 16, or 24 for faster motion. 12 looks choppy. |
| FFN chunking | **off** | dev default off. Splits the model's feed-forward step to cut peak VRAM. **Turn on for 0.7 MP and above on 16 GB cards** (0.8 MP ran out of VRAM without it). Slightly slower; marked experimental. Chunk count (4) is set inside the subgraph. |
| color match strength | **0.75** loop · **0** I2V | dev: 0.75 when used. Keep it on for loops (stops the washed-out end and the flash at the loop point). |
| model upscale | **off** | AnimeSharpV4 doubles each side. Slow; sharpens line art, can harden soft shading. |
| RTX upscale | **off** | NVIDIA RTX Video Super Resolution doubles each side. Fast and mild. When on it is used *instead of* the upscale model. Needs `nvidia-vfx` (see [install](install.md)). Mode, quality and scale are inside the subgraph (*RTX upscale* node: VSR / Ultra / 2.0; try *High Bitrate* mode for a softer, cleaner result). |
| interpolation multiplier | **1 (off)** | 2 = double fps with RIFE (built-in ComfyUI node, `rife_v4.26`). At 1 the step is skipped entirely. Loops stay seamless when interpolated. Leave at 1 while testing. |

**Inside the subgraph** (developer defaults that rarely change; double-click the subgraph node to open it):

- *Sample high-noise steps → noise seed*: random on every run (*control after generate* = randomize). Set a number and switch to *fixed* to repeat a result or to compare settings.
- Model files are picked on the loader nodes: *Load high-noise model*, *Load low-noise model*, *Load text encoder*, *Load VAE*, *Load upscale model* (**2x-AnimeSharpV4_RCAN**), *Load interpolation model* (**rife_v4.26**).
- *Total steps*: **4** and *Split step*: **2** (dev: 4 steps for the distilled model, split at half).
- *CFG*: **1** (dev: 1–1.5). 1 is fastest and ignores the negative prompt.
- *Set shift (high)* and *Set shift (low)*: **5** (dev: 5, valid 5–10). Change both.
- *Sample high-noise steps* and *Sample low-noise steps* → sampler / scheduler: **euler / simple** (dev: always works; euler/linear_quadratic or uni_pc_bh2/simple as alternatives). Change both.
- *Apply NAG (high)* and *Apply NAG (low)* → nag_scale: **11** (dev). Used when **negative** is on.
- *Scale to megapixels → resolution_steps*: **16** (closest to the image's shape) or **32** (the developer's Div32).
- *Attention backend* nodes (one per model): **comfy kitchen attention** (dev default, faster INT8 attention). Set to *pytorch attention* to turn off.
