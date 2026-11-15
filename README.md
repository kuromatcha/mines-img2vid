# mines-img2vid

ComfyUI image-to-video workflows for **DaSiWa WAN 2.2 I2V 14B v11**, set up with the model developer's own defaults, plus one reference-to-video workflow with audio for **DaSiWa MiniMax H3**.

| Workflow | Makes | Needs |
|---|---|---|
| **Mine's Loop NVFP4** | Seamless loop | RTX 50-series |
| **Mine's I2V NVFP4** | Image to video | RTX 50-series |
| **Mine's Loop Painter NVFP4** | Seamless loop with the PainterFLF2V node (motion boost) | RTX 50-series |
| **Mine's I2V Painter NVFP4** | Image to video with the PainterI2V node (motion boost, no end image) | RTX 50-series |
| **Mine's Long NVFP4** | Longer video, one prompt per 5 s segment (SVI 2.0 Pro) | RTX 50-series |
| **Mine's Ref2VA W4A8** | Video with sound from up to 3 reference images (MiniMax H3, a different model: see [Ref2VA](docs/settings.md#ref2va-workflow-minimax-h3)) | 16 GB+ GPU, about 28 GB RAM plus page file |

The GGUF versions were dropped: they gave the same results as NVFP4 at about half the speed. The WAN workflows therefore need an RTX 50-series card.

> **Needs [mines-pack](https://github.com/kuromatcha/mines-pack)**, this project's own node pack (color drift fix, keep colors after RTX upscale, optional image loader, SVIPro end frame). Clone it into `ComfyUI/custom_nodes/` and restart ComfyUI; without it every workflow shows missing nodes. It replaces the `ComfyUI-DaSiWa-EndFrame` folder that used to ship here.

## Quick start

1. Install ComfyUI, the node packs (including **mines-pack**) and the models: [docs/install.md](docs/install.md)
2. Drag a file from [`workflows/`](workflows) into ComfyUI.
3. Load your image, write a prompt, keep the defaults and run.

## Docs

- [Install](docs/install.md): hardware, node packs, model downloads, launch settings
- [Settings](docs/settings.md): what each setting does and the recommended values (including the Ref2VA workflow)
- [Recommended practice](docs/practice.md): test-then-render routine, prompting tips, measured speed
- [Troubleshooting](docs/troubleshooting.md): out-of-memory, loop flash, mouth movement, missing nodes
- [Camera and motion tests](docs/camera-tests.md): why the camera stays still, getting more motion, what was tried and dropped
- [Tools](tools/README.md): build a Long workflow with more segments, tidy the layout

Model files are not included (DaSiWa may not be redistributed).
