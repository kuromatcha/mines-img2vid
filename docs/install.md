# Install

Everything a new PC needs to run the workflows.

## Hardware (tested setup)

- NVIDIA RTX 5070 Ti 16 GB, 32 GB RAM, Windows 11, NVMe SSD.
- **16 GB VRAM** is the practical minimum. **32 GB RAM** works; 64 GB is more comfortable.
- NVFP4 workflows need an **RTX 50-series (Blackwell)** card. Use the GGUF workflows on anything else.
- Disk: about 30 GB for one model set (GGUF *or* NVFP4) plus 7 GB of shared files.

## ComfyUI

- **Comfy Desktop with ComfyUI 0.45.3 or newer** (tested on 0.45.3, PyTorch 2.12.1 + CUDA 13.0, Python 3.13).
  Several built-in nodes used here (Transfer Color, Switch, Math Expression, Model Attention Backend, NAG, Wan First-Last-Frame, Frame Interpolation) only exist in recent versions.
- RTX 50-series needs the **CUDA 13 (cu130)** PyTorch build. Comfy Desktop installs it automatically.

## Custom node packs

Install with ComfyUI-Manager ("Install Custom Nodes") or `git clone` into `ComfyUI/custom_nodes/`, then restart.

| Pack | Needed for | Source |
|---|---|---|
| **ComfyUI-GGUF** | GGUF model loader (GGUF workflows) | https://github.com/city96/ComfyUI-GGUF |
| **ComfyUI-DaSiWa-Nodes** | `Seamless Loop` node (loop workflows), `RTX Upscaler & Refiner` node (optional RTX upscale, all 4 workflows) | https://github.com/darksidewalker/ComfyUI-DaSiWa-Nodes |
| **ComfyUI-KJNodes** | `Wan Chunk FeedForward` node (optional FFN chunking, all 4 workflows) | https://github.com/kijai/ComfyUI-KJNodes |

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
| `unet/` | `DasiwaWAN22I2V14BLightspeed_snatchkissHighV11-Q6_K.gguf` | 11.2 GB | [darksidewalker/DaSiWa-WAN2.2-I2V](https://huggingface.co/darksidewalker/DaSiWa-WAN2.2-I2V) → `Distilled/GGUF/v11/` **(gated)** |
| `unet/` | `DasiwaWAN22I2V14BLightspeed_snatchkissLowV11-Q6_K.gguf` | 11.2 GB | same |
| `diffusion_models/` | `DasiwaWAN22I2V14BLightspeed_snatchkissHighV11-NVFP4.safetensors` | 7.8 GB | same repo → `Distilled/NVFP4/v11/` **(gated, RTX 50 only)** |
| `diffusion_models/` | `DasiwaWAN22I2V14BLightspeed_snatchkissLowV11-NVFP4.safetensors` | 7.8 GB | same |
| `text_encoders/` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6.3 GB | [Comfy-Org/Wan_2.2_ComfyUI_Repackaged](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged) → `split_files/text_encoders/` |
| `vae/` | `wan_2.1_vae.safetensors` | 0.24 GB | same repo → `split_files/vae/` |
| `frame_interpolation/` | `rife_v4.26.safetensors` | 23 MB | [Comfy-Org/frame_interpolation](https://huggingface.co/Comfy-Org/frame_interpolation) → `frame_interpolation/` (used by Seamless Loop and by the optional interpolation in all 4 workflows) |
| `upscale_models/` | `2x-AnimeSharpV4_RCAN.safetensors` | 31 MB | [Kim2091/2x-AnimeSharpV4](https://huggingface.co/Kim2091/2x-AnimeSharpV4) *(optional upscale)* |

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
