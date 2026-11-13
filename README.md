# DaSiWa video workflows (ComfyUI)

Four image-to-video workflows built on **DaSiWa WAN 2.2 I2V 14B v11 "SnatchKiss" (Lightspeed)**, wired to the model developer's own defaults (Darksidewalker, workflow *FastFidelity C-AiO-95*).

| Workflow | What it makes | Model files |
|---|---|---|
| **DaSiWa Loop GGUF** | Seamless loop (same image as first and last frame) | Q6_K GGUF, any NVIDIA GPU |
| **DaSiWa Loop NVFP4** | Same, faster on RTX 50-series | NVFP4, **RTX 50-series only** |
| **DaSiWa I2V GGUF** | Normal image-to-video (start frame only) | Q6_K GGUF |
| **DaSiWa I2V NVFP4** | Same, faster on RTX 50-series | NVFP4, **RTX 50-series only** |

Only install the model files for the versions you will use (GGUF, NVFP4 or both).

**Repository layout:** `workflows/` holds the four workflow files (drag one into ComfyUI or copy them to `ComfyUI/user/default/workflows/`). `tools/` holds the scripts that built them (see `tools/README.md`). Model files are not included; section 1 lists where to download each one.

---

## 1. What you need to reinstall

### Hardware (tested setup)

- NVIDIA RTX 5070 Ti 16 GB, 32 GB RAM, Windows 11, NVMe SSD.
- **16 GB VRAM** is the practical minimum. **32 GB RAM** works; 64 GB is more comfortable.
- NVFP4 workflows need an **RTX 50-series (Blackwell)** card. Use the GGUF workflows on anything else.
- Disk: about 30 GB for one model set (GGUF *or* NVFP4) plus 7 GB of shared files.

### ComfyUI

- **Comfy Desktop with ComfyUI 0.45.3 or newer** (tested on 0.45.3, PyTorch 2.12.1 + CUDA 13.0, Python 3.13).
  Several built-in nodes used here (Transfer Color, Switch, Math Expression, Model Attention Backend, NAG, Wan First-Last-Frame) only exist in recent versions.
- RTX 50-series needs the **CUDA 13 (cu130)** PyTorch build. Comfy Desktop installs it automatically.

### Custom node packs

Install with ComfyUI-Manager ("Install Custom Nodes") or `git clone` into `ComfyUI/custom_nodes/`, then restart.

| Pack | Needed for | Source |
|---|---|---|
| **ComfyUI-GGUF** | GGUF model loader (GGUF workflows) | https://github.com/city96/ComfyUI-GGUF |
| **ComfyUI-Frame-Interpolation** | `RIFE VFI` node (optional interpolation, all 4 workflows) | https://github.com/Fannovel16/ComfyUI-Frame-Interpolation |
| **ComfyUI-DaSiWa-Nodes** | `Seamless Loop` node (loop workflows) | https://github.com/darksidewalker/ComfyUI-DaSiWa-Nodes |
| **ComfyUI-KJNodes** | `Wan Chunk FeedForward` node (optional FFN chunking, all 4 workflows) | https://github.com/kijai/ComfyUI-KJNodes |

ComfyUI-DaSiWa-Nodes lists heavy extras in its `requirements.txt` (LLM, RTX, AMD tools). **Seamless Loop does not need them.** The pack loads without installing them; they only load when you use those other nodes. If an installer insists, skipping `llama-cpp-python` is fine (it often fails to build on Windows).

### Model files

All paths are inside `ComfyUI/models/` (or your shared models folder).

| Folder | File | Size | Source |
|---|---|---|---|
| `unet/` | `DasiwaWAN22I2V14BLightspeed_snatchkissHighV11-Q6_K.gguf` | 11.2 GB | [darksidewalker/DaSiWa-WAN2.2-I2V](https://huggingface.co/darksidewalker/DaSiWa-WAN2.2-I2V) → `Distilled/GGUF/v11/` **(gated)** |
| `unet/` | `DasiwaWAN22I2V14BLightspeed_snatchkissLowV11-Q6_K.gguf` | 11.2 GB | same |
| `diffusion_models/` | `DasiwaWAN22I2V14BLightspeed_snatchkissHighV11-NVFP4.safetensors` | 7.8 GB | same repo → `Distilled/NVFP4/v11/` **(gated, RTX 50 only)** |
| `diffusion_models/` | `DasiwaWAN22I2V14BLightspeed_snatchkissLowV11-NVFP4.safetensors` | 7.8 GB | same |
| `text_encoders/` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6.3 GB | [Comfy-Org/Wan_2.2_ComfyUI_Repackaged](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged) → `split_files/text_encoders/` |
| `vae/` | `wan_2.1_vae.safetensors` | 0.24 GB | same repo → `split_files/vae/` |
| `frame_interpolation/` | `rife_v4.26.safetensors` | 23 MB | [Comfy-Org/frame_interpolation](https://huggingface.co/Comfy-Org/frame_interpolation) → `frame_interpolation/` (used by Seamless Loop) |
| `upscale_models/` | `2x-AnimeSharpV4_RCAN.safetensors` | 31 MB | [Kim2091/2x-AnimeSharpV4](https://huggingface.co/Kim2091/2x-AnimeSharpV4) *(optional upscale)* |
| *(automatic)* | `rife49.pth` | — | downloaded by ComfyUI-Frame-Interpolation on first use of `RIFE VFI` |

**Gated DaSiWa repo:** log in to Hugging Face, open the repo page and accept the access request. Then either download in the browser, or log in once from a terminal with ComfyUI's Python and download from there:

```powershell
& "<ComfyUI>\.venv\Scripts\python.exe" -m huggingface_hub.cli.hf auth login
```

(In PowerShell the `&` in front of the quoted path is required.) The developer asks that the model is not redistributed; download it from the original page.

### Launch settings (Comfy Desktop → installation settings → launch arguments)

```
--enable-manager --reserve-vram 0.5 --listen --fast fp16_accumulation
```

- `--fast fp16_accumulation`: faster math, as in the developer's workflow (on by default there).
- **Do not use `--disable-dynamic-vram`.** On this setup it made model loading crash with "Windows fatal exception: access violation".

### Windows page file

With 32 GB RAM, give Windows room to spill. Set it yourself (system setting), then restart Windows:

1. `Win + R` → `sysdm.cpl` → **Advanced** → Performance **Settings…** → **Advanced** → Virtual memory **Change…**
2. Untick *Automatically manage…*
3. **C:** → *System managed size* → **Set**
4. Another fast drive (e.g. **D:**) → *Custom size* 32768 / 49152 MB → **Set** (the drive's line must show the new sizes before you press OK)
5. OK → restart Windows

---

## 2. Settings (front panel of each workflow)

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
| interpolation multiplier | **1 (off)** | 2 = double fps with RIFE. Leave at 1 while testing. |

**Inside the subgraph (advanced):**

- *Scale to megapixels → resolution_steps*: **16** (closest to the image's shape) or **32** (the developer's Div32).
- *Attention backend* nodes (one per model): **comfy kitchen attention** (dev default, faster INT8 attention). Set to *pytorch attention* to turn off.

---

## 3. Recommended practice

**Workflow choice**

- Loops → **DaSiWa Loop**. Anything that should end in a different pose → **DaSiWa I2V**.
- RTX 50-series → try **NVFP4** first (smaller, fits more of the model in VRAM). Keep the **GGUF** version as the fallback.

**Before you render**

- Start ComfyUI fresh. Don't run other big workflows (e.g. other video models) in the same session first. Leftover models fill RAM and VRAM.
- Close GPU-heavy apps (browser hardware acceleration, Discord, Steam). More free VRAM means less of the model spills into system RAM.

**Iterate cheaply, then render once**

1. **Smoke test:** megapixels **0.3**, duration **3 s**, color match / upscale / interpolation off. About a minute per try.
2. Change prompt or seed until the motion is right.
3. **Final:** same seed, megapixels **0.6** (or 0.8), duration **5 s**, color match on for loops, then optional upscale and interpolation.
   Motion changes a little with size and length, but stays close.

**Prompting (this model)**

- Describe the motion you want; the model follows the prompt more than the negative prompt.
- To keep the mouth still, say it in the prompt: *"closed-mouth smile, lips stay closed and still, no talking"*. Avoid phrases like "smile widens". If the mouth still moves, turn **NAG** on.
- For loops, describe a repeating motion that *"ends in the same pose it started in"*. Subtle, cyclic motion loops best.
- Detailed, soft-rendered illustration keeps its look best at **0.6 MP or higher**. Below that, fine lines blur.

**After editing a workflow file outside ComfyUI**

- Close its open tab **without saving** and reopen it from the workflows list, otherwise the old tab overwrites the file.

---

## 4. Measured on the test PC (RTX 5070 Ti 16 GB, 32 GB RAM, Q6_K GGUF, 5 s at 16 fps)

| Size | Time per video | Seconds per step |
|---|---|---|
| 608×880 (≈0.54 MP) | ~3.1 min | ~32 s |
| 640×928 (≈0.6 MP) | — | ~29 s |
| 704×1024 (≈0.72 MP) | ~4.8 min | ~51 s |

These were measured before Comfy Kitchen attention and fp16 accumulation were added. NVFP4 was not measured yet.

---

## 5. Troubleshooting

| Problem | Fix |
|---|---|
| *Allocation on device 0 would exceed allowed memory* during sampling | Video memory too small for that size. Turn **FFN chunking** on, or lower megapixels. **Restart ComfyUI after any out-of-memory error** (a run right after one produced broken NaN frames). |
| *Seamless Loop input contains NaN or infinity* | Broken frames, usually right after an out-of-memory error. Restart ComfyUI and run again. If it repeats in a fresh session, remove `--fast fp16_accumulation`. |
| Crash: *Windows fatal exception: access violation* while loading a model | Out of memory. Restart ComfyUI before rendering, enlarge the page file, don't use `--disable-dynamic-vram`. |
| Loop "flashes" white at the loop point | Keep **color match** on (0.75) and the **Seamless Loop** node active; keep duration at 5 s (16 fps). |
| Mouth keeps moving | Prompt for closed, still lips; turn **NAG** on. |
| Red "missing node" boxes | Install the custom node pack from section 1 and restart. |
| NVFP4 workflow errors or is slow | Needs an RTX 50-series GPU and PyTorch built for CUDA 13; otherwise use the GGUF workflows. |
| Model files missing in dropdowns | Check the folders in section 1, then press **R** in ComfyUI or restart it. |
