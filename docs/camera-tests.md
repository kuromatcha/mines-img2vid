# Camera and motion tests

Results from testing on the setup in [setup](setup.md#1-check-your-hardware) (RTX 5070 Ti 16 GB, 32 GB RAM), November 2026. They explain some of the advice in [practice](practice.md); none of them changes a workflow default. Each comparison used one start image, one prompt and one seed, so read them as strong hints, not as measurements across many clips.

## Why the camera tends to stay still

1. **Distilled model, 4 steps at CFG 1.** DaSiWa Lightspeed has the lightx2v speed-up merged in, which users widely report damps large motion, camera moves most of all. With only 2 high-noise steps, camera and body motion compete, and at CFG 1 the prompt pulls weakly.
2. **Camera line late in the prompt.** In the usual order (subject → motion → camera → scene) the camera comes third and gets little attention.
3. **Plain backgrounds.** A zoom or pan only shows against a background. Without one, the model moves the character instead.
4. **Fixed end frames.** An end image fixes the last frame's framing, Loop forces the last frame to match the first, and in Long the SVI LoRA anchors each segment to the start image.

## Camera prompt test

Loop workflow, white background, 6 s at 16 fps, 0.8 MP, same seed. The test prompt put a push-in that eases back out *first*, followed by a gentle sway.

*Zoom* is the largest scale change against the first frame (1.00 = none). *Body motion* is optical flow after removing the camera movement (higher = more movement), given as the average and the clip's thirds.

| Model | Prompt | Shift | Zoom | Body motion |
|---|---|---|---|---|
| v11 NVFP4 | camera line last | 8 | 1.02 | 3.2 (2.8 / 3.7 / 3.0) |
| v11 NVFP4 | camera line first | 10 | 1.23 | 1.5 (1.7 / 1.6 / 1.3) |
| v11 GGUF Q6 | camera line first | 10 | 1.47 | 1.8 (2.3 / 2.0 / 1.1) |
| v9 GGUF Q6 | camera line first | 10 | 1.23 | 5.2 (5.2 / 5.3 / 5.0) |

- **Put the camera line first.** With it last, the framing never changed.
- **v11 trades body motion for camera motion.** It zooms, but the sway nearly stops, most of all in the last third.
- **v9 SynthSeduction did both** and kept more body motion than any v11 run. The workflows still use v11 (better detail and prompt following); v9 is no longer part of this project.
- **The mouth opened mid-clip in every camera run**, on both versions. Turning on NAG in the low-noise steps as well (tested on v9) did not stop it.

## More body motion: PainterFLF2V

[ComfyUI-PainterFLF2V](https://github.com/princepainter/ComfyUI-PainterFLF2V) replaces *Wan First-Last-Frame to Video* and adds a `motion_amplitude` setting (1.0 = same as the stock node). This test was run with the node swapped into the Loop workflow by hand. It led to the **Mine's Loop Painter NVFP4** workflow, which ships with amplitude 1.15 ([settings](settings.md#painter-nvfp4-i2v-and-loop)). The node only has an effect when an end image is connected, so in Loop or in I2V with an end image.

Loop NVFP4 (v11), same image, seed and sway prompt (no camera line), 0.8 MP, shift 5:

| Amplitude | Body motion | Zoom | Time |
|---|---|---|---|
| 1.0 (stock) | 3.6 (3.8 / 3.9 / 2.9) | none | 231 s |
| 1.15 | 4.6 (4.8 / 5.0 / 4.2) | none | 227 s |
| 1.3 | 5.5 (5.5 / 5.9 / 5.0) | none | 224 s |

- Motion rises steadily (+31% at 1.15, +54% at 1.3) and the last third no longer dies down. At 1.3, v11 moves as much as v9 did.
- The character design and colors hold at both settings, and there is no slowdown.
- At 1.3 the face gets livelier and the mouth opens once.
- Not part of this test: I2V and Long. PainterI2V (no end image) was tested later for the Painter workflows; see [settings](settings.md#painter-nvfp4-i2v-and-loop).

## LTX 2.3 (DaSiWa DragonLeap v4): dropped

Three runs at 0.5 MP, 5 s, 24 fps. LTX is fast (88–123 s per clip) and fits in 16 GB VRAM, but:

- **The camera is not promptable.** It ignored a push-in once and added one unasked once.
- **The style only held with gentle settings** (the developer's own sampling and refine strengths), which also calmed the motion to below Wan v9.

It was removed and is not part of this project.

## Leads not tested

- **Wan 2.2 Fun Camera Control:** a separate model with pan, zoom and orbit presets, without DaSiWa's anime training.
- **Uni3C:** copies a camera path from a reference video; the core node was built for Wan 2.1.
- **Index-AniSora V3.2** (Bilibili): an anime video model built on Wan 2.2, with first, middle and last frame control.
- **Camera LoRAs:** Civitai has Wan 2.2 I2V dolly-zoom and crash-zoom LoRAs for the high-noise model only.
- **A start image with a real background**, so a camera move has something to show against.
