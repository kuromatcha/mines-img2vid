# mines-video

ComfyUI image-to-video workflows, ready to run with tested defaults.

- **WAN 2.2** (DaSiWa WAN 2.2 I2V 14B v11): silent video from a start image.
- **MiniMax H3**: video with sound from reference images, a first and last frame, or both.

## Workflows

| Workflow | What you get | Model |
|---|---|---|
| **Mine's I2V NVFP4** | Video from a start image, optional end image | WAN 2.2 |
| **Mine's Loop NVFP4** | Seamless loop | WAN 2.2 |
| **Mine's I2V Painter NVFP4** | I2V with more motion (PainterI2V), no end image | WAN 2.2 |
| **Mine's Loop Painter NVFP4** | Loop with more motion (PainterFLF2V) | WAN 2.2 |
| **Mine's Long NVFP4** | Longer video, one prompt per 5 s segment | WAN 2.2 + SVI 2.0 Pro |
| **Mine's Ref2VA INT8** | Video with sound from up to 3 reference images | DaSiWa MiniMax H3 |
| **Mine's FL2VA NVFP4** | Video with sound from a first frame, optional last frame | MiniMax H3 (base) |
| **Mine's Hybrid INT8** | Video with sound: first/last frame plus up to 3 references | DaSiWa MiniMax H3 |

## Requirements

- **GPU:** 16 GB VRAM. The NVFP4 workflows need an RTX 50-series card; the two INT8 workflows do not.
- **RAM:** 32 GB plus a Windows page file. The MiniMax H3 workflows load about 28–36 GB.
- **ComfyUI** 0.45.3 or newer.
- **[mines-pack](https://github.com/kuromatcha/mines-pack)**, this project's node pack. Every workflow needs it.

Model files are not included. The DaSiWa models may not be redistributed, so download them from their original pages.

## Quick start

1. Follow the [setup guide](docs/setup.md): node packs, models, launch settings.
2. Drag a file from [`workflows/`](workflows) into ComfyUI.
3. Load your image, write a prompt, keep the defaults and run.

## Docs

| | |
|---|---|
| [Setup](docs/setup.md) | Hardware, node packs, model downloads, launch settings, page file |
| [Settings](docs/settings.md) | What each setting does and the recommended values, per workflow |
| [Recommended practice](docs/practice.md) | Test-then-render routine, prompting tips, measured speed |
| [Troubleshooting](docs/troubleshooting.md) | Out of memory, loop flash, mouth movement, missing nodes |
| [Camera and motion tests](docs/camera-tests.md) | Why the camera stays still, how to get more motion, what was tried and dropped |
| [Tools](tools/README.md) | Build a Long workflow with more segments, tidy a layout, stitch clips |
