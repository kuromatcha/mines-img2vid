# Camera motion tests (2026-11-14)

Test notes for future reference, not a recommended setting yet. Question: why does the model not zoom or follow, and does another DaSiWa version do better?

## Why the camera stays still (research)

1. **Distilled model, 4 steps at CFG 1.** DaSiWa "Lightspeed" has the lightx2v/Lightning speed-up merged in. Users widely report that it damps large motion, camera moves most of all. With 2 high-noise steps, camera and body motion compete for the same small budget. At CFG 1 the prompt pulls weakly and image-to-video falls back to keeping the start framing.
2. **Prompts asked for a still camera.** Earlier test prompts said "the camera holds still on a locked-off shot". In the developer's order (subject → motion → camera → scene) the camera comes late and gets less attention.
3. **Plain white backgrounds.** A zoom or follow is only visible against a background (parallax). With none, the model moves the character instead.
4. **End image / Loop / Long pin the framing.** An end image fixes the last frame's framing. Loop forces the last frame to equal the first. In Long, the SVI LoRA anchors every segment to the start image.
5. **Shift 5 is the cautious end.** Higher shift allows bigger changes (dev range 5–10).

Other routes (not tried):

- **Wan 2.2 Fun Camera**: separate model with pan, zoom and orbit presets. Nodes `WanCameraEmbedding` and `WanCameraImageToVideo` are in core ComfyUI; it does not use DaSiWa weights.
- **Uni3C**: copies a camera path from a reference video. The core `WanUni3CControlnetApply` node was built for Wan 2.1; untested on 2.2.
- **Three-sampler setup**: a first high-noise pass at CFG 2–3.5 without the speed-up. It needs the non-distilled model, because DaSiWa's speed-up is merged in.

## DaSiWa versions

All on [darksidewalker/DaSiWa-WAN2.2-I2V](https://huggingface.co/darksidewalker/DaSiWa-WAN2.2-I2V) (gated). The motion notes are user reports from [civarchive](https://civarchive.com/models/1981116). The developer's comparison article ([Civitai](https://civitai.com/articles/23495/dasiwa-model-versions-and-timeline)) needs a login.

| Version | Type | Formats | User reports on motion |
|---|---|---|---|
| v11 SnatchKiss (current) | distilled, 4 steps | GGUF, NVFP4, FP8 | best prompt following; very expressive, random mouth movement |
| v10 BoundBite | distilled | GGUF, NVFP4, FP8 | consistent; slower motion |
| **v9 SynthSeduction** | distilled | GGUF, FP8 | strongest motion, "realistic camera shake"; slower in SVI (Long) |
| v8 TastySin | distilled | GGUF, FP8 | steady normal pace, liked in SVI |
| v1–v7 | distilled | FP8 only | no notes |
| Truevision v9 / v10 / v11 | **non-distilled**, 20–30 steps, real CFG | FP8 only (14.5–19.5 GB each) | not tested; about 5–7× slower |

Downloaded for the tests: `DasiwaWAN22I2V14BSynthseduction_q6High.gguf` and `..._q6Low.gguf` (12.0 GB each, `Distilled/GGUF/v09/`, in `models/unet/`).

## Test setup

- Loop workflow, start image `34.png` (office woman, white background, high angle). 6 s, 16 fps, 0.8 MP, interpolation ×2, color match 0.75, FFN chunking on, negative (NAG high) on, RTX upscale on. Same seed in every run.
- **Camera prompt** (camera first, a push-in that comes back out so it fits a loop):

  > The camera slowly pushes in toward the woman's upper body, then eases back out to the full body shot it started from. She stays in place and sways gently, a slow weight shift from one leg to the other, her torso rocking slightly and her shoulders rising and falling with calm breathing. Her hands keep their grip on the open shirt, the fabric shifting softly. Loose strands of hair sway against her cheek. She holds her smile with closed, still lips. Plain white background with a soft floor shadow, soft even lighting.

- Negative prompt: the workflow default plus `static camera, locked-off shot`.
- Shift 10 (baseline: 8).

**How it was measured**

- *Zoom*: scale of each frame against frame 0, from ORB feature matching (1.00 means no zoom).
- *Body motion*: 90th-percentile optical flow between frames 4 apart, after the global camera transform is removed. Higher means more body movement. The three numbers are the clip's thirds.

## Results

| Clip (`output/video/`) | Model | Prompt / shift | Max zoom | Body motion (thirds) |
|---|---|---|---|---|
| `DaSiWa_nvfp4_loop_00001_` | v11 NVFP4 | camera last, shift 8 (baseline) | 1.02 | 3.2 (2.8 / 3.7 / 3.0) |
| `cam_test_loop_00001_` | v11 NVFP4 | camera first, shift 10 | 1.23 | 1.5 (1.7 / 1.6 / 1.3) |
| `cam_v11_gguf_00001_` | v11 GGUF Q6 | camera first, shift 10 | 1.47 | 1.8 (2.3 / 2.0 / 1.1) |
| `cam_v9_gguf_00001_` | **v9 GGUF Q6** | camera first, shift 10 | 1.23 | **5.2 (5.2 / 5.3 / 5.0)** |
| `cam_v9_naglow2_00001_` | v9 GGUF Q6 | same + NAG (low) on | 1.24 | 5.1 (5.1 / 5.1 / 5.1) |

**What the results show**

- **The camera line has to come first.** With the camera line last (baseline) the framing never changes.
- **v11 trades body motion for camera motion.** It zooms, but the sway almost stops, especially in the last third.
- **v9 does both.** A smooth push-in and return, with the sway and breathing kept, even more body motion than the still-camera baseline. Hands and design hold.
- **The mouth opens mid-clip in every camera run** (toothy smile at the closest point), on both versions.

## LTX 2.3 test (DaSiWa LTX 2.3 DragonLeap v4)

- Model: `DaSiWa-LTX23-DragonLeap-v4_Q4_K.gguf` (13.0 GB, Civitai, SHA256 checked) in `models/unet`. Gemma 3 12B heretic fp8 (`text_encoders`), `ltx-2.3_text_projection_bf16` and `LTX23_audio_vae_bf16` (both in `checkpoints`, the LTX loaders read only that folder), `LTX23_video_vae_bf16` (`vae`), `ltx-2.3-spatial-upscaler-x2-1.1` (`latent_upscale_models`).
- Workflow: *DaSiWa LTX I2V (test)*, ComfyUI user workflows only (built by a scratch script, not in this repo). Same front panel as the Wan I2V. Two passes as in the official LTX 2.3 I2V template: half size with 8 distilled steps, then a 2× latent upscale and 3 refine steps. CFG 1, `euler_cfg_pp`, seed 42.
- Prompt: the same idea in the developer's LTX style (one flowing sentence, "the view eases slowly inward … and drifts back out", sounds next to their source).
- Run: 0.5 MP (576×896), 5 s, 24 fps, FFN chunking on. **88 s**, no errors, fits in 16 GB VRAM / 32 GB RAM. The output includes an audio track.

| Clip | Max zoom | Body motion (thirds) |
|---|---|---|
| `cam_ltx_v4_05mp_00002_` | none (pulls *out* to 0.83, unsteady) | 5.9 (7.6 / 5.8 / 4.6) |

**What the frames show**
- **No push-in.** The framing wobbles and pulls back instead.
- **Lots of motion, not what the prompt asked for.** She straightens up out of the forward lean, her hands let go of the shirt and drift down to the hem, and the shirt closes.
- **The design drifts.** The bun disappears, the face turns semi-realistic and the eyes change: the "fine detail shifting" the developer lists as a known LTX issue.
- **The mouth stays closed**, unlike every Wan camera run.
- **Fast:** 88 s at 0.5 MP, against about 4 min for Wan v9 at 0.8 MP.

**Second run: simpler prompt, still view** (`ltx_v4_still_05mp_00001_`, same settings and seed). The prompt names her look first (black hair in a low bun, white shirt held open over a black lace bra), asks for "leans slightly forward … sways gently … hands keeping their firm grip", and ends with "the view holding still from above".

| Clip | Max zoom | Body motion (thirds) |
|---|---|---|
| `ltx_v4_still_05mp_00001_` | 1.18 (a gentle push-in, **not asked for**) | 4.0 (4.3 / 4.3 / 3.4) |

- **The design holds this time.** Bun, face, lean and pose stay. Hands keep their grip. The mouth stays closed (one wink).
- **Steady sway**, a little less than Wan v9 (5.2).
- **It pushed in anyway**, although the prompt said the view holds still. Camera moves seem to come easily to LTX, but they don't follow the prompt reliably.
- **Takeaway:** for LTX, describe the character's look and pose plainly in the prompt. In run 1 the model reinterpreted a pose described only through motion. Next test: a camera prompt in this simpler style.

**Third run: the developer's settings** (`ltx_v4_devset_05mp_00001_`). Sources: his LTX workflow *OmniForge C-LTX23 v5.1* ([GitHub](https://github.com/darksidewalker/dasiwa-comfyui-workflows/tree/main/C-LTX23)) and his LTX prompt guide ([PromptForge `prompts/video/ltx.md`](https://github.com/darksidewalker/PromptForge-Public)).

Changes from runs 1–2:

1. **Prompt opens with the style:** "A hand-drawn 2D anime shot in clean cel shading with crisp black line art, seen from a high angle…". Then scene, character, action, camera ("slowly pushes in and settles on her upper body"), sound, as his guide orders it.
2. **His sampling:** `linear_quadratic`. Pass 1 has 8 steps at full denoise. A 2× latent upscale follows, then **4 steps at denoise 0.4**, then **2 steps at 0.2**. Runs 1–2 used the official template's refine from 0.85, which repaints most of the image.
3. **Start image at strength 1.0** in every pass (was 0.7 in pass 1).
4. **Color match** to the start image at 0.75 (new front-panel setting, as in the Wan workflows).

| Clip | Max zoom | Body motion (thirds) | Time |
|---|---|---|---|
| `ltx_v4_devset_05mp_00001_` | 1.04 (no push-in) | 3.5 (3.5 / 3.3 / 3.5) | 123 s |

- **The style holds.** Clean anime line art and cel shading in every frame. Face, bun, earring, mole, lean and grip all stay, and the mouth stays closed. This is the first LTX run that looks like the start image throughout.
- **Still no push-in**, although the prompt asks for one. Run 2 pushed in unasked. The camera is not reliably promptable on LTX either.
- **Motion is gentler** (3.5, against 4.0 in run 2 and 5.2 for Wan v9) and steady.
- Not yet tried: the developer's text encoder (Gemma heretic **v2**; we use v1), his 900p size, and other seeds.

**Verdict (2026-11-14): LTX dropped.** It doesn't do the job here: the camera is not promptable, and the style only holds with gentle settings that also calm the motion. The LTX model, Gemma encoder, VAEs, text projection, latent upscaler and the test workflow were moved to the Recycle Bin (29.1 GB). Only the test clips in `output/video` remain.

## Chinese community: alternatives (research, 2026-11-14)

Searched Bilibili, Zhihu, CSDN and LiblibAI. On Chinese sites, DaSiWa is the anime Wan 2.2 model people recommend most (v9 is praised for fixing Wan's slow motion). None of the leads below has been tested here.

1. **PainterI2V / PainterFLF2V** (by princepainter, [GitHub](https://github.com/princepainter/ComfyUI-PainterI2V), now in [ComfyUI-PainterNodes](https://github.com/princepainter/ComfyUI-PainterNodes)). It replaces the image-to-video conditioning node and adds a `motion_amplitude` setting (1.0 = stock node, about 1.15–1.3 recommended), made to fix the slow motion of 4-step distilled models. It is the fix most often recommended on Chinese sites for "动作慢". The author says it also makes camera prompts more responsive. Our workflows use `WanFirstLastFrameToVideo`, so the matching node is **PainterFLF2V** (1.0–2.0, 1.2–1.3 everyday). This is the cheapest test: no new model, one node swap. The claims are the author's own and untested on DaSiWa.
2. **Index-AniSora** by Bilibili ([GitHub](https://github.com/bilibili/index-anisora), Apache 2.0). An anime-only video model. **V3.2 (2025-09) is built on Wan 2.2**, with 8-step inference, first, middle and last frame control, and a 360° character turnaround. V3.1 has a wider motion range, and a 12 GB VRAM version is on ModelScope. A GGUF build is at `QuantStack/Index-Anisora-V3.2-GGUF` and runs with the core GGUF loader. No camera control is advertised. Community reports are mixed (one bad Q8 result on a 3090; a guide uses 30 steps at CFG 5.5, which is slow).
3. **Wan 2.2 Fun Camera Control** (Alibaba). The Chinese tutorials (CSDN, Bilibili BV1tmYqzQECv) say the same as the English docs: preset push, pull and pan without prompt tricks, but the 4-step LoRA reduces motion, and the model has no DaSiWa anime training.
4. **Camera LoRAs**: no dedicated Chinese push-in LoRA for Wan 2.2 turned up. On Civitai there are Wan 2.2 I2V *dolly zoom* and *crash zoom* LoRAs for high noise only; the push-in LoRA (lovis93) is for Wan 2.1.
5. **Wan2.2-Remix**: a general-purpose finetune that is popular in Chinese one-click bundles and said to handle anime and game CG styles. No anime camera tests found.

## PainterFLF2V test (body motion, 2026-11-14)

Installed `ComfyUI-PainterFLF2V` (commit c81a68f) and `ComfyUI-PainterI2V` (c46e480) in `custom_nodes`, code only (no dependencies, reviewed). The saved workflows are unchanged: for the test, the queued prompt swapped `WanFirstLastFrameToVideo` (inside the Loop subgraph) for `PainterFLF2V` with the same inputs plus `motion_amplitude`.

- How it works: it encodes the usual start, gray and end frames, then boosts the high-frequency part of the difference between the gray middle and a straight blend of start and end. Colour (low frequency) is left alone. **It only does anything when an end image is connected** (Loop, or I2V with an end image). For I2V without an end image, use `PainterI2V` instead (untested).
- Setup: Loop NVFP4 (v11), `34.png`, 6 s, 16 fps, 0.8 MP, interpolation ×2, colour match 0.75, chunking, NAG (high), RTX upscale, shift 5 (workflow default), same seed. The prompt is the sway prompt with no camera line.

| Clip (`output/video/`) | Amplitude | Body motion (thirds) | Zoom | Colour drift | Time |
|---|---|---|---|---|---|
| `painter_loop_a100_00001_` | 1.0 (= stock node) | 3.6 (3.8 / 3.9 / 2.9) | none | 12.2 | 231 s |
| `painter_loop_a115_00001_` | 1.15 | **4.6** (4.8 / 5.0 / 4.2) | none | 13.3 | 227 s |
| `painter_loop_a130_00001_` | 1.3 | **5.5** (5.5 / 5.9 / 5.0) | none | 13.3 | 224 s |

(Colour drift: the largest LAB channel shift of the figure against frame 0.)

- **Motion rises steadily:** +31% at 1.15 and +54% at 1.3. The last third no longer dies down. At 1.3, v11 moves as much as v9 did (5.2).
- **Design holds** at both settings: bun, grip on the shirt, mole and outfit stay the same. There's no extra colour shift and no slowdown.
- **At 1.3 the face gets livelier:** more head tilt, and the mouth opens in one part of the clip. The baseline also shows a toothy smile once.
- Verdict: worth keeping. 1.15 is the safe setting, and 1.3 suits when more motion is wanted.

Not yet tested: I2V (with and without an end image), Long, and v9 + PainterFLF2V.

## Workflow note found during testing

The front-panel input named **`switch`** is *Switch: model upscale*, not a NAG switch. *Switch: NAG (low)* (node 179) has no front-panel input; turn it on inside the subgraph. Run `cam_v9_naglow_00001_` was meant to test NAG (low) but had model upscale on instead, so it doesn't count.

## Open

- **Mouth:** NAG (low) on v9 (`cam_v9_naglow2`) did not stop the mouth opening; the clip is nearly the same as without it. Next ideas: drop "smile" from the prompt (use "calm expression, lips pressed together"), or lower shift to 8 on v9.
- Non-distilled Truevision v11 (real CFG): not tested.
- A start image with a real background (parallax): not tested.
