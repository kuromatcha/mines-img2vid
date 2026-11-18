# Setup

Everything a new PC needs to run the workflows. Do the steps in order; steps 3 and 4 only need the parts for the workflows you want.

1. [Check your hardware](#1-check-your-hardware)
2. [Install ComfyUI](#2-install-comfyui)
3. [Install the node packs](#3-install-the-node-packs)
4. [Download the models](#4-download-the-models)
5. [Set the launch arguments](#5-set-the-launch-arguments)
6. [Enlarge the Windows page file](#6-enlarge-the-windows-page-file)
7. [First run](#7-first-run)

## 1. Check your hardware

| | Needed | Notes |
|---|---|---|
| GPU | 16 GB VRAM | The NVFP4 workflows need an **RTX 50-series** card. The two INT8 workflows (Ref2VA, Hybrid) run on other 16 GB cards. |
| RAM | 32 GB | Works with a page file (step 6). 64 GB is more comfortable. |
| Disk | about 24 GB for WAN (27 GB with Long) | MiniMax H3 adds about 40 GB for Ref2VA and Hybrid, and 12.5 GB more for FL2VA. A fast SSD shortens model loading. |

Tested on: RTX 5070 Ti 16 GB, 32 GB RAM, Windows 11, NVMe SSD.

## 2. Install ComfyUI

Install **Comfy Desktop** with ComfyUI **0.45.3 or newer**. Tested on 0.45.3 and 0.45.4 with PyTorch 2.12.1 + CUDA 13.0 and Python 3.13.

- An RTX 50-series card needs the CUDA 13 (cu130) PyTorch build. Comfy Desktop installs it automatically.
- Older ComfyUI versions lack built-in nodes these workflows use (MiniMax H3, NAG, Wan First-Last-Frame, Frame Interpolation and others).

## 3. Install the node packs

Install with ComfyUI-Manager (**Install Custom Nodes**), or `git clone` into `ComfyUI/custom_nodes/`. Restart ComfyUI afterwards.

| Pack | Needed by | Install |
|---|---|---|
| [mines-pack](https://github.com/kuromatcha/mines-pack) | **All workflows** | `git clone https://github.com/kuromatcha/mines-pack.git` (not in Manager) |
| [ComfyUI-DaSiWa-Nodes](https://github.com/darksidewalker/ComfyUI-DaSiWa-Nodes) | All workflows (RTX upscale node); Loop workflows (Seamless Loop node) | Manager or git |
| [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) | All workflows (FFN chunking); Long (segment join) | Manager or git |
| [ComfyUI-PainterI2V](https://github.com/princepainter/ComfyUI-PainterI2V) | Mine's I2V Painter NVFP4 only | Manager or git |
| [ComfyUI-PainterFLF2V](https://github.com/princepainter/ComfyUI-PainterFLF2V) | Mine's Loop Painter NVFP4 only | `git clone https://github.com/princepainter/ComfyUI-PainterFLF2V.git` (not in Manager) |

Notes:

- ComfyUI-DaSiWa-Nodes lists heavy extras in its `requirements.txt` (LLM, RTX and AMD tools). The nodes used here do not need them, and the pack loads without them. If an installer insists, skipping `llama-cpp-python` is fine; it often fails to build on Windows.
- If you copied the old `ComfyUI-DaSiWa-EndFrame` folder from an earlier version of this repository into `custom_nodes/`, delete it. Its nodes moved to mines-pack.

### RTX upscale (optional)

The **RTX upscale** switch needs NVIDIA's `nvidia-vfx` package (about 435 MB, NVIDIA RTX cards only). Close ComfyUI, install it into ComfyUI's Python, then start ComfyUI again:

```powershell
& "<ComfyUI>\.venv\Scripts\python.exe" -m pip install nvidia-vfx
```

Tested with `nvidia-vfx` 0.2.0.0. Without it the workflows still load and run; only switching RTX upscale on gives an error.

## 4. Download the models

All folders are inside `ComfyUI/models/` (or your shared models folder).

### WAN 2.2 workflows (I2V, Loop, Painter, Long)

| Folder | File | Size | Source |
|---|---|---|---|
| `diffusion_models/` | `DasiwaWAN22I2V14BLightspeed_snatchkissHighV11-NVFP4.safetensors` | 7.8 GB | [darksidewalker/DaSiWa-WAN2.2-I2V](https://huggingface.co/darksidewalker/DaSiWa-WAN2.2-I2V) → `Distilled/NVFP4/v11/` (gated, see below) |
| `diffusion_models/` | `DasiwaWAN22I2V14BLightspeed_snatchkissLowV11-NVFP4.safetensors` | 7.8 GB | same |
| `text_encoders/` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6.3 GB | [Comfy-Org/Wan_2.2_ComfyUI_Repackaged](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged) → `split_files/text_encoders/` |
| `vae/` | `wan_2.1_vae.safetensors` | 0.24 GB | same repo → `split_files/vae/` |
| `frame_interpolation/` | `rife_v4.26.safetensors` | 23 MB | [Comfy-Org/frame_interpolation](https://huggingface.co/Comfy-Org/frame_interpolation) → `frame_interpolation/` |

**Long workflow only**, also:

| Folder | File | Size | Source |
|---|---|---|---|
| `loras/` | `SVI_v2_PRO_Wan2.2-I2V-A14B_HIGH_lora_rank_128_fp16.safetensors` | 1.23 GB | [Kijai/WanVideo_comfy](https://huggingface.co/Kijai/WanVideo_comfy/tree/main/LoRAs/Stable-Video-Infinity/v2.0) |
| `loras/` | `SVI_v2_PRO_Wan2.2-I2V-A14B_LOW_lora_rank_128_fp16.safetensors` | 1.23 GB | same |

**The DaSiWa repo is gated.** Log in to Hugging Face, open the repo page and accept the access request. Then download in the browser, or log in once from a terminal and download from there:

```powershell
& "<ComfyUI>\.venv\Scripts\python.exe" -m huggingface_hub.cli.hf auth login
```

In PowerShell the `&` in front of the quoted path is required.

### MiniMax H3 workflows (Ref2VA, FL2VA, Hybrid)

Shared by all three:

| Folder | File | Size | Source |
|---|---|---|---|
| `text_encoders/` | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15.69 GB | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) → `text_encoders/` |
| `vae/` | `minimax_h3_video_vae_int8_convrot.safetensors` | 2.81 GB | [Kijai/MiniMax-H3-experimental](https://huggingface.co/Kijai/MiniMax-H3-experimental) |
| `vae/` | `minimax_h3_audio_vae_fp32.safetensors` | 0.6 GB | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) → `vae/` |
| `frame_interpolation/` | `rife_v4.26.safetensors` | 23 MB | same file as in the WAN table |

Plus one model, depending on the workflow:

| Workflow | Folder | File | Size | Source |
|---|---|---|---|---|
| Ref2VA, Hybrid | `diffusion_models/` | `dasiwa_minimax_h3_ref2va_v5xs_pruned_graviton_int8_row-wise_convrot_runtime_mixed.safetensors` | 20.48 GB | [Civitai: DaSiWa MiniMax H3](https://civitai.com/models/2877206), version "DaSiWa GXS v5", the int8 file (not Turbo). Needs a Civitai login. |
| FL2VA | `diffusion_models/` | `MiniMax_H3_FL2VA_pruned_nvfp4.safetensors` | 12.53 GB | [Abiray/Minimax-H3-nvfp4-INT4-INT8-Convrot](https://huggingface.co/Abiray/Minimax-H3-nvfp4-INT4-INT8-Convrot) |

Model plus text encoder is about 36 GB for Ref2VA and Hybrid and about 28 GB for FL2VA. With 32 GB of RAM this relies on the page file, and the first run is slow.

The RIFE file is only used when interpolation is above 1, but ComfyUI reports it as missing at load while it is absent, because its loader node is in the graph.

## 5. Set the launch arguments

Comfy Desktop → installation settings → launch arguments:

```
--enable-manager --reserve-vram 0.5 --listen --fast fp16_accumulation
```

- `--fast fp16_accumulation` is faster math, as in the model developer's own workflow.
- `--listen` makes ComfyUI reachable from other devices on your network. Leave it out if you only use ComfyUI on this PC.
- **Do not use `--disable-dynamic-vram`.** On the test PC it made model loading crash with *Windows fatal exception: access violation*.

## 6. Enlarge the Windows page file

With 32 GB of RAM, Windows needs room to spill over.

1. `Win + R` → `sysdm.cpl` → **Advanced** → Performance **Settings…** → **Advanced** → Virtual memory **Change…**
2. Untick *Automatically manage…*
3. **C:** → *System managed size* → **Set**
4. Another fast drive (e.g. **D:**) → *Custom size* 32768 / 49152 MB → **Set**. The drive's line must show the new sizes before you press OK.
5. **OK**, then restart Windows.

## 7. First run

1. Start ComfyUI and drag a file from [`workflows/`](../workflows) onto the canvas. No red "missing node" boxes should show; if they do, see [troubleshooting](troubleshooting.md).
2. Pick your image on **Start image** (or **Reference 1** / **First frame**).
3. For a quick test, set **megapixels** to 0.3 and **duration** to 3, then run. A WAN test clip takes about a minute once the models are loaded.
4. For the full routine and prompt tips, see [recommended practice](practice.md). For what each setting does, see [settings](settings.md).
