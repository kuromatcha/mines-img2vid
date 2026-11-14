# Recommended practice

**Workflow choice**

- Loops → **Mine's Loop**. Anything that should end in a different pose → **Mine's I2V**.
- RTX 50-series → use **NVFP4**: about twice as fast as GGUF, with slightly softer fine detail (see *Measured speed*). Use **GGUF** on other cards, or for a final render where the last bit of detail matters.

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
- For a camera move (push-in, pan), put the camera line **first**. Placed third, as in the guide above, it was ignored in testing, and the camera move costs body motion ([tests](camera-tests.md)).
- To keep the mouth still, say it in the prompt: *"closed-mouth smile, lips stay closed and still, no talking"*. Avoid phrases like "smile widens". If the mouth still moves, turn **negative** on.
- For loops, describe a repeating motion that *"ends in the same pose it started in"*. Subtle, cyclic motion loops best.
- Detailed, soft-rendered illustration keeps its look best at **0.6 MP or higher**. Below that, fine lines blur.

**After editing a workflow file outside ComfyUI**

- Close its open tab **without saving** and reopen it from the workflows list, otherwise the old tab overwrites the file.

## Measured speed

Test PC: RTX 5070 Ti 16 GB, 32 GB RAM. Loop workflow, 640×976 (0.6 MP), 5 s at 16 fps, color match on, other extras off, default sampling (4 steps, euler / simple). Times are for a full run after a warm-up run, so the models had already been loaded once.

| Model | One 5 s loop | Per sampling step |
|---|---|---|
| NVFP4 | **71 s** | about 12.6 s |
| GGUF Q6_K | **150 s** | about 24–29 s |

GGUF spends about 25–40 s of each run moving its larger model in and out of video memory. With the same seed, NVFP4 moved slightly more and kept the loop just as seamless, with about 8% less fine detail (hard to see in playback).
