# Install

Everything a new PC needs to run the workflows.

## Hardware (tested setup)

- NVIDIA RTX 5070 Ti 16 GB, 32 GB RAM, Windows 11, NVMe SSD.
- **16 GB VRAM** is the practical minimum. **32 GB RAM** works; 64 GB is more comfortable.
- The WAN workflows (I2V, Loop, Long) use NVFP4 models and need an **RTX 50-series (Blackwell)** card. Older versions of this repository had GGUF workflows for other cards; they were dropped (same results, about half the speed).
- Disk: about 16 GB for the NVFP4 models plus 7 GB of shared files.

## ComfyUI

- **Comfy Desktop with ComfyUI 0.45.3 or newer** (tested on 0.45.3, PyTorch 2.12.1 + CUDA 13.0, Python 3.13).
  Several built-in nodes used here (Transfer Color in the Long workflows, Switch, Math Expression, Model Attention Backend, NAG, Wan First-Last-Frame, Frame Interpolation) only exist in recent versions.
- RTX 50-series needs the **CUDA 13 (cu130)** PyTorch build. Comfy Desktop installs it automatically.

## Custom node packs

Install with ComfyUI-Manager ("Install Custom Nodes") or `git clone` into `ComfyUI/custom_nodes/`, then restart.

**mines-pack is required.** It holds this project's own nodes (the optional image loader, the SVIPro end frame, color drift fix and keep source colors). Without it every workflow opens with missing nodes. It replaces the `ComfyUI-DaSiWa-EndFrame` folder that used to ship in this repository: if you copied that folder into `ComfyUI/custom_nodes/` before, delete it, since those old nodes are no longer used.

| Pack | Needed for | Source |
|---|---|---|
| **ComfyUI-DaSiWa-Nodes** | `Seamless Loop` node (loop workflows), `RTX Upscaler & Refiner` node (optional RTX upscale, all workflows) | https://github.com/darksidewalker/ComfyUI-DaSiWa-Nodes |
| **mines-pack** (shows as *mine's pack*) | **Required by all workflows.** `color drift fix` (I2V, Loop and Hybrid workflows); `keep source colors` (after the RTX upscale, all workflows); `load image (optional)` (end image, I2V and Long workflows; references, Ref2VA and Hybrid workflows; last frame, FL2VA and Hybrid workflows); `H3 frame guides` (Hybrid workflow); `SVIPro end frame` (Long workflows); on Windows also hides the harmless WinError 10054 console traceback ([troubleshooting](troubleshooting.md)) | https://github.com/kuromatcha/mines-pack — `git clone https://github.com/kuromatcha/mines-pack.git` (not listed in ComfyUI-Manager) |
| **ComfyUI-PainterI2V** | `PainterI2V` node (Mine's I2V Painter NVFP4) | https://github.com/princepainter/ComfyUI-PainterI2V |
| **ComfyUI-PainterFLF2V** | `PainterFLF2V` node (Mine's Loop Painter NVFP4). A separate pack from PainterI2V | https://github.com/princepainter/ComfyUI-PainterFLF2V — `git clone https://github.com/princepainter/ComfyUI-PainterFLF2V.git` (not listed in ComfyUI-Manager) |
| **ComfyUI-KJNodes** | `Wan Chunk FeedForward` node (optional FFN chunking, all workflows) and `MiniMax Chunk FeedForward` (Ref2VA, FL2VA and Hybrid workflows); `Wan Image To Video SVIPro` and `Image Batch Extend With Overlap` (Long workflows) | https://github.com/kijai/ComfyUI-KJNodes |

ComfyUI-DaSiWa-Nodes lists heavy extras in its `requirements.txt` (LLM, RTX, AMD tools). **Seamless Loop does not need them.** The pack loads without installing them; they only load when you use those other nodes. If an installer insists, skipping `llama-cpp-python` is fine (it often fails to build on Windows).

### RTX upscale (optional)

The **RTX upscale** toggle needs NVIDIA's `nvidia-vfx` package (about 435 MB, NVIDIA RTX GPU only) in ComfyUI's Python environment. Close ComfyUI, install it, then start ComfyUI again:

```powershell
& "<ComfyUI>\.venv\Scripts\python.exe" -m pip install nvidia-vfx
```

Tested with `nvidia-vfx` 0.2.0.0. Without the package the workflows still load and run; only turning the RTX toggle on gives an error.

## Model files

All paths are inside `ComfyUI/models/` (or your shared models folder).

| Folder | File | Size | Source |
|---|---|---|---|
| `diffusion_models/` | `DasiwaWAN22I2V14BLightspeed_snatchkissHighV11-NVFP4.safetensors` | 7.8 GB | [darksidewalker/DaSiWa-WAN2.2-I2V](https://huggingface.co/darksidewalker/DaSiWa-WAN2.2-I2V) → `Distilled/NVFP4/v11/` **(gated, RTX 50 only)** |
| `diffusion_models/` | `DasiwaWAN22I2V14BLightspeed_snatchkissLowV11-NVFP4.safetensors` | 7.8 GB | same |
| `text_encoders/` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6.3 GB | [Comfy-Org/Wan_2.2_ComfyUI_Repackaged](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged) → `split_files/text_encoders/` |
| `vae/` | `wan_2.1_vae.safetensors` | 0.24 GB | same repo → `split_files/vae/` |
| `frame_interpolation/` | `rife_v4.26.safetensors` | 23 MB | [Comfy-Org/frame_interpolation](https://huggingface.co/Comfy-Org/frame_interpolation) → `frame_interpolation/` (used by Seamless Loop and by the optional interpolation in all WAN workflows) |
| `loras/` | `SVI_v2_PRO_Wan2.2-I2V-A14B_HIGH_lora_rank_128_fp16.safetensors` | 1.23 GB | [Kijai/WanVideo_comfy](https://huggingface.co/Kijai/WanVideo_comfy/tree/main/LoRAs/Stable-Video-Infinity/v2.0) → `LoRAs/Stable-Video-Infinity/v2.0/` *(Long workflows)* |
| `loras/` | `SVI_v2_PRO_Wan2.2-I2V-A14B_LOW_lora_rank_128_fp16.safetensors` | 1.23 GB | same |

### Ref2VA workflow (MiniMax H3)

**Mine's Ref2VA INT8** uses a different model family. It needs ComfyUI 0.45.3 or newer with the native MiniMax H3 nodes, plus the KJNodes, mines-pack and DaSiWa-Nodes packs above (it uses `MiniMax Chunk FeedForward`, `load image (optional)` and the RTX upscaler). No NVFP4 card is needed. The model plus the text encoder are about 36 GB, so on 32 GB of RAM it relies on the page file and the first run is slow.

| Folder | File | Size | Source |
|---|---|---|---|
| `diffusion_models/` | `dasiwa_minimax_h3_ref2va_v5xs_pruned_graviton_int8_row-wise_convrot_runtime_mixed.safetensors` | 20.48 GB | [Civitai: DaSiWa MiniMax H3](https://civitai.com/models/2877206), version "DaSiWa GXS v5", the int8 file (not the Turbo version; needs a Civitai login) |
| `text_encoders/` | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15.69 GB | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) → `text_encoders/` |
| `vae/` | `minimax_h3_video_vae_int8_convrot.safetensors` | 2.81 GB | [Kijai/MiniMax-H3-experimental](https://huggingface.co/Kijai/MiniMax-H3-experimental) |
| `vae/` | `minimax_h3_audio_vae_fp32.safetensors` | 0.6 GB | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) → `vae/` |
| `frame_interpolation/` | `rife_v4.26.safetensors` | 23 MB | same as above *(interpolation)* |

The RIFE file is only used when **interpolate** is above 1, but ComfyUI lists it as missing at load while it is absent, because the loader node is in the graph.

### FL2VA workflow (MiniMax H3)

**Mine's FL2VA NVFP4** uses the base MiniMax H3 first/last-frame model. (DaSiWa's models are hybrids that also take first/last frames: that is the Hybrid workflow below.) Same requirements as the Ref2VA workflow, plus an RTX 50-series card for the NVFP4 model. The text encoder, VAEs and RIFE file are the same as in the Ref2VA table; only the model differs. Model plus text encoder are about 28 GB.

| Folder | File | Size | Source |
|---|---|---|---|
| `diffusion_models/` | `MiniMax_H3_FL2VA_pruned_nvfp4.safetensors` | 12.53 GB | [Abiray/Minimax-H3-nvfp4-INT4-INT8-Convrot](https://huggingface.co/Abiray/Minimax-H3-nvfp4-INT4-INT8-Convrot) |

### Hybrid workflow (MiniMax H3)

**Mine's Hybrid INT8** uses the same files as the Ref2VA workflow (no extra download): DaSiWa's model takes references and first/last frames in one clip. It needs a current **mines-pack** for the `H3 frame guides` node.

**Gated DaSiWa repo:** log in to Hugging Face, open the repo page and accept the access request. Then either download in the browser, or log in once from a terminal with ComfyUI's Python and download from there:

```powershell
& "<ComfyUI>\.venv\Scripts\python.exe" -m huggingface_hub.cli.hf auth login
```

(In PowerShell the `&` in front of the quoted path is required.) The developer asks that the model is not redistributed; download it from the original page.

## Launch settings (Comfy Desktop → installation settings → launch arguments)

```
--enable-manager --reserve-vram 0.5 --listen --fast fp16_accumulation
```

- `--fast fp16_accumulation`: faster math, as in the developer's workflow (on by default there).
- **Do not use `--disable-dynamic-vram`.** On this setup it made model loading crash with "Windows fatal exception: access violation".

## Windows page file

With 32 GB RAM, give Windows room to spill. Set it yourself (system setting), then restart Windows:

1. `Win + R` → `sysdm.cpl` → **Advanced** → Performance **Settings…** → **Advanced** → Virtual memory **Change…**
2. Untick *Automatically manage…*
3. **C:** → *System managed size* → **Set**
4. Another fast drive (e.g. **D:**) → *Custom size* 32768 / 49152 MB → **Set** (the drive's line must show the new sizes before you press OK)
5. OK → restart Windows
