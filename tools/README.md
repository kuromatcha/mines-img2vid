# tools

Two scripts that work on the workflows in `../workflows` as they are now. Run them with ComfyUI's Python, and back up the workflow first. After editing a workflow file outside ComfyUI, close its open tab without saving and reopen it from the workflows list.

## `dasiwa_long.py`: Long workflow with more segments

Builds a Long workflow from an I2V workflow, with one prompt and one optional end image per 5-second segment (2 to 12 segments). It adds the SVI 2.0 Pro LoRAs, chains the segments and joins them with a short cross-fade. Run the layout script on the result.

```
python -I tools/dasiwa_long.py "workflows/Mine's I2V GGUF.json" "workflows/Mine's Long GGUF.json" 4
python -I tools/dasiwa_layout.py "workflows/Mine's Long GGUF.json"
```

Use the NVFP4 I2V workflow to get the NVFP4 Long workflow. The output file is overwritten. With 2 segments, the result matches the Long workflows in this repository.

## `dasiwa_layout.py`: tidy layout

Places every node inside the subgraph by its title, one group per stage (Models, Input, Timing, Sampling, High noise, Low noise, Segment N, Decode, Upscale, Interpolate, Video). On the front, it puts the image loaders, settings, video and Guide in one row, all 960 px tall on the 20 px snap grid (images and video 480 wide, settings 640, Guide 560). It checks that the wiring is unchanged, and stops if a node has no place. Safe to run any number of times.

```
python -I tools/dasiwa_layout.py "workflows/Mine's Loop GGUF.json"
```

## How the workflows were built

The workflows started from the original Wan 2.2 loop workflow and were changed step by step with one-off scripts, which are no longer in this repository. Their history is in the git log.
