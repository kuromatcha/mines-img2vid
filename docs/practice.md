# Recommended practice

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

## Measured speed

Test PC: RTX 5070 Ti 16 GB, 32 GB RAM, Q6_K GGUF, 5 s at 16 fps.

| Size | Time per video | Seconds per step |
|---|---|---|
| 608×880 (≈0.54 MP) | ~3.1 min | ~32 s |
| 640×928 (≈0.6 MP) | — | ~29 s |
| 704×1024 (≈0.72 MP) | ~4.8 min | ~51 s |

These were measured before Comfy Kitchen attention and fp16 accumulation were added. NVFP4 was not measured yet.
