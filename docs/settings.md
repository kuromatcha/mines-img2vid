# Settings

Values in **bold** are the defaults in these workflows. The setting names match the front panel; the **Guide** note in each workflow has the short version of this page. "dev" means the DaSiWa developer's recommendation.

| Setting | Default | Suggestion |
|---|---|---|
| prompt | your text | Structure (dev): 1) subject, 2) motion, 3) camera, 4) scene. One paragraph, 80–120 words, most of them on motion. See [Recommended practice](practice.md). |
| negative prompt | "talking, speaking, mouth moving…" | Only has an effect when **negative** is on (or CFG is above 1, inside the subgraph). |
| end image | **none** | Optional (I2V and Long). The pose the clip ends on, e.g. the front view of a character who turns, or a different pose from a character sheet. At **none** it is skipped and the clip ends wherever the motion goes. Use an image with the same framing, background, outfit and art style as the start image; a mismatch gives a morph or cross-fade instead of motion. A different aspect ratio is center-cropped to the start image's shape. The prompt should describe the motion that gets from the start pose to the end pose. |
| negative | **off** | Turns on NAG in the high-noise steps, which makes the negative prompt work at CFG 1, e.g. to stop mouth movement. Motion is set in those steps, so this covers most of the effect. NAG doubles the time of each step it runs on (measured: 30 → 60 s per step at 1.0 MP), so with only the high-noise half it costs about 1.5× the sampling time. Dev default off; uses more VRAM. |
| megapixels | **0.6** | **0.3** smoke test · **0.6** baseline · **0.8** HD (dev range 0.52–0.83). Keeps the image's shape, any ratio. |
| duration (seconds) | **5** | dev: **5 s at 16 fps** (or 3 s at 24 fps) is Wan 2.2's native length; longer clips drift and wash out. |
| fps | **16** | dev: 16, or 24 for faster motion. 12 looks choppy. |
| shift | **5** | dev: 5, valid 5–10. Sets both *Set shift* nodes (high and low) inside the subgraph. Higher spends more of the steps on the overall shape: bigger motion and layout changes. Lower keeps closer to the start image. |
| FFN chunking | **off** | dev default off. Splits the model's feed-forward step to cut peak VRAM. **Turn on for 0.7 MP and above on 16 GB cards** (0.8 MP ran out of VRAM without it). Slightly slower; marked experimental. Chunk count (4) is set inside the subgraph. |
| color match strength | **0.5** | Mode is **uniform** (inside the subgraph, *Match colors to start image*): one correction for the whole clip, worked out from all its frames. It fixes the lifted, washed-out blacks but keeps natural light changes during the motion. The old per-frame 0.75 locked every frame to the start image's brightness and pushed contrast a bit past it, which looked harsh. Keep it on for loops (stops the flash at the loop point); 0 turns it off. |
| model upscale | **off** | AnimeSharpV4 doubles each side. Slow; sharpens line art, can harden soft shading. |
| RTX upscale | **off** | NVIDIA RTX Video Super Resolution doubles each side. Fast and mild. When on it is used *instead of* the upscale model. Needs `nvidia-vfx` (see [install](install.md)). Mode, quality and scale are inside the subgraph (*RTX upscale* node: High Bitrate / Ultra / 2.0). High Bitrate suits the clean decoded frames; *VSR* mode is meant for compressed video and sharpens edges and blocks into visible noise here. |
| interpolation multiplier | **1 (off)** | 2 = double fps with RIFE (built-in ComfyUI node, `rife_v4.26`). At 1 the step is skipped entirely. Loops stay seamless when interpolated. Leave at 1 while testing. |

**Inside the subgraph** (developer defaults that rarely change; double-click the subgraph node to open it):

- *Sample high-noise steps → noise seed*: random on every run (*control after generate* = randomize). Set a number and switch to *fixed* to repeat a result or to compare settings.
- Model files are picked on the loader nodes: *Load high-noise model*, *Load low-noise model*, *Load text encoder*, *Load VAE*, *Load upscale model* (**2x-AnimeSharpV4_RCAN**), *Load interpolation model* (**rife_v4.26**).
- *Total steps*: **4** and *Split step*: **2** (dev: 4 steps for the distilled model, split at half). Tested: 6 steps split at 3 took about 30% longer with no visible gain.
- *CFG*: **1** (dev: 1–1.5). 1 is fastest and ignores the negative prompt.
- *Sample high-noise steps* and *Sample low-noise steps* → sampler / scheduler: **euler / simple** (dev: always works; euler/linear_quadratic or uni_pc_bh2/simple as alternatives). Change both. Tested on Loop: uni_pc_bh2/simple looked the same as euler/simple; euler/linear_quadratic was a little sharper but left a visible jump at the loop point, drifted more in color and opened the mouth wider.
- *Apply NAG (high)* and *Apply NAG (low)* → nag_scale: **11** (dev).
- *Switch: NAG (low)*: **off**. Turn on to apply NAG in the low-noise steps too (full NAG, about 2× the sampling time), if the mouth still opens or shows teeth with **negative** on.
- *Scale to megapixels → resolution_steps*: **16** (closest to the image's shape) or **32** (the developer's Div32).
- *Attention backend* nodes (one per model): **comfy kitchen attention** (dev default, faster INT8 attention). Set to *pytorch attention* to turn off.

## Long workflows

Same settings as I2V, plus:

| Setting | Default | Suggestion |
|---|---|---|
| prompt 1, prompt 2, … | your text | One prompt per segment. Describe only that segment's motion; repeat camera and scene in each. The next segment continues from where the last one ended. |
| end image 1, end image 2, … | **none** | Optional end pose for each segment. A segment at **none** ends freely; either way the next segment continues from the last frames of the one before. |
| segment length (seconds) | **5** | Length of each segment. Keep 5 (81 frames); longer segments wash out colors. |
| color match strength | **0.75**, per frame | Stronger than in I2V and Loop, and matched per frame, on purpose: contrast fades segment by segment, and only per-frame matching pulls each part back. Without it, a 4-segment test lost 25% contrast and 16% saturation by the last segment; at 0.75 the loss was 6% and 4%. In a 2-segment test, uniform 0.5 let the end fade to 86% contrast, against 95% with per-frame 0.75. |

**Inside the subgraph:**

- *Apply SVI LoRA (high)* and *(low)*: **1.0**. The SVI 2.0 Pro LoRAs that keep the character and the motion going across segments.
- *Build segment N latent (SVI)* → motion_latent_count: **1** (how much of the previous segment is carried over).
- *Join segment N*: overlap **5**. A new segment starts by replaying the last 5 frames of the previous one; the two copies are cross-faded, so each extra segment adds 76 new frames (4.75 s).
- *Sample high-noise steps (segment N)*: each segment has its own seed.
- More segments: rebuild with `tools/dasiwa_long.py` (see [Tools](../tools/README.md)).

## Ref2VA workflow (MiniMax H3)

**Mine's Ref2VA W4A8** makes a video with sound from up to 3 reference images, with the DaSiWa GXS v5 Turbo model (W4A8 build). Models: [install](install.md#ref2va-workflow-minimax-h3). It has not been rendered end to end yet; the values below are the developer's and the model's own.

| Setting | Default | Suggestion |
|---|---|---|
| reference 1, 2, 3 | 1 required, 2 and 3 **none** | Reference 1 sets the aspect ratio and is `<Picture 1>` in the prompt. Numbers follow the slots that are filled: with only 1 and 3, reference 3 is `<Picture 2>`. A reference can be a character, a place, a style or a pose, not only a first frame. |
| prompt | example prompt | Six sections, each a heading followed by text: `subject_definitions`, `summary` (starts with *reference generation.*), `retention_analysis` (`fully_preserved`, `partially_preserved`, `attribute_transfer`, `weak_reference`), `detailed_description` (`[Shot 1]`, a later cut as `[Shot 2] At 00:03.000 …`), `overall_soundscape` (dialogue in quotes) and `non_diegetic_music` (or *N/A*). If the prompt does not say what to keep, the model invents a background: name it as a subject and list it as `fully_preserved`, in one short line. Long lists of things not to show can make them appear. |
| megapixels | **0.6** | **0.3** test · **0.6** normal · **0.8** high. Trained around 0.8 (native: 768 px short edge, capped near 1 MP). Turn FFN chunking on from about 0.7 MP. |
| duration (seconds) | **5** | Trained on 5–15 s. The frame count is rounded up to a multiple of 17, plus 5. |
| fps | **24** | Keep 24: the model is trained at 24 fps, and changing it changes the frame count and the speed of the motion. |
| interpolate | **1 (off)** | 2 doubles the fps with RIFE (48 fps). |
| steps | **6** | 4 fast preview (rough audio) · 6 basic · 8 quality. For the non-turbo build (`…ref2va_v5xs_pruned_graviton_w4a8`): 20–25 steps, sampler *res_multistep*, shift 10–12. |
| shift | **8** | Video shift, turbo range 6–12. The audio shift is fixed at 4 (*Set shift*, inside the subgraph). |
| FFN chunking | **off** | Less VRAM, slower. On from about 0.7 MP. |
| RelayVSR 2x | **off** | 2× video upscale trained on H3 clips, one sampling step; only every 15th frame goes through the model. Output is 2× per side. |
| RTX 2x | **off** | 2× RTX Video Super Resolution (needs `nvidia-vfx`, see [install](install.md)). Fast and mild; overrides RelayVSR 2x if both are on. |
| mute audio | **off** | Saves the video without a sound track; the audio is not decoded at all. |

**Inside the subgraph:** *Sampler* **euler** / *Scheduler* **simple**, CFG 1, no negative prompt (turbo model; for the non-turbo model set *Sampler* to res_multistep). *Seed* is random; set *fixed* to keep one. Reference size in *Build conditioning from references*: **match** (*max* keeps the identity sharper but is much slower). Model files are picked on the *Load …* nodes. Routine: test at 0.3 MP, 5 s, 4 steps with the extras off; rerun until the motion is right, fix the seed; then render at 0.6 MP and 8 steps and add upscale or interpolation.
