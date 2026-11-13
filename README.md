# mines-img2vid

ComfyUI image-to-video workflows for **DaSiWa WAN 2.2 I2V 14B v11**, set up with the model developer's own defaults.

| Workflow | Makes | Needs |
|---|---|---|
| **DaSiWa Loop GGUF** | Seamless loop | any NVIDIA GPU, 16 GB+ |
| **DaSiWa Loop NVFP4** | Seamless loop, faster | RTX 50-series |
| **DaSiWa I2V GGUF** | Image to video | any NVIDIA GPU, 16 GB+ |
| **DaSiWa I2V NVFP4** | Image to video, faster | RTX 50-series |
| **DaSiWa Long GGUF** | Longer video, one prompt per 5 s segment (SVI 2.0 Pro) | any NVIDIA GPU, 16 GB+ |
| **DaSiWa Long NVFP4** | Longer video, faster | RTX 50-series |

## Quick start

1. Install ComfyUI, the node packs and the models: [docs/install.md](docs/install.md)
2. Drag a file from [`workflows/`](workflows) into ComfyUI.
3. Load your image, write a prompt, keep the defaults and run.

## Docs

- [Install](docs/install.md): hardware, node packs, model downloads, launch settings
- [Settings](docs/settings.md): what each setting does and the recommended values
- [Recommended practice](docs/practice.md): test-then-render routine, prompting tips, measured speed
- [Troubleshooting](docs/troubleshooting.md): out-of-memory, loop flash, mouth movement, missing nodes
- [Tools](tools/README.md): the scripts that built the workflows

Model files are not included (DaSiWa may not be redistributed).
