# Recommended practice

**Workflow choice**

- Loops → **Mine's Loop**. Anything that should end in a different pose → **Mine's I2V**.
- RTX 50-series → try **NVFP4** first (smaller, fits more of the model in VRAM). Keep the **GGUF** version as the fallback.

**Before you render**

- Start ComfyUI fresh. Don't run other big workflows (e.g. other video models) in the same session first. Leftover models fill RAM and VRAM.
- Close GPU-heavy apps (browser hardware acceleration, Discord, Steam). More free VRAM means less of the model spills into system RAM.

**Iterate cheaply, then render once**

1. **Smoke test:** megapixels **0.3**, duration **3 s**, color match / upscale / interpolation off. About a minute per try.
2. Change the prompt, or run again for a new seed, until the motion is right. When you like a result, fix its seed inside the subgraph (*Sample high-noise steps*: set *control after generate* to *fixed*).
3. **Final:** with the seed fixed, megapixels **0.6** (or 0.8), duration **5 s**, color match on for loops, then optional upscale and interpolation.
   Motion changes a little with size and length, but stays close.

**Prompting (this model)**

The developer's prompt guide (from ComfyUI-DaSiWa-Nodes, `data/llm_skills/wan.md`):

- One paragraph of plain sentences, **80–120 words**, in this order: **subject → motion → camera → scene**. Wan pays most attention to what comes first.
- **Subject:** name it briefly with two or three identifying details. The start image already shows the rest, so do not describe it again.
- **Motion:** spend the most words here. Write verbs in sequence and say how each is done (slowly, sharply, hesitantly). Give the clip **one continuous action** with a beginning and an end; a list of separate events blurs together in five seconds.
- **Camera:** one move, or holding still, with framing and angle. Two moves fight each other.
- **Scene:** two or three concrete objects and the light, kept short.
- Describe only what can be seen. If the idea is thin on motion, add small movements: hair moving, a glance, a breath, light shifting.

From testing these workflows:

- The model follows the prompt more than the negative prompt.
- To keep the mouth still, say it in the prompt: *"closed-mouth smile, lips stay closed and still, no talking"*. Avoid phrases like "smile widens". If the mouth still moves, turn **negative** on.
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
