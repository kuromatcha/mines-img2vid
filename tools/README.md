# tools

Run these with ComfyUI's Python. `dasiwa_long.py` and `dasiwa_layout.py` edit the workflows in `../workflows`: back up the workflow first, and after editing a workflow file outside ComfyUI, close its open tab without saving and reopen it from the workflows list.

## `dasiwa_stitch.py`: join clips into one video or a seamless loop

Joins finished clips in the order given, cross-fading 5 frames at each join (the same join the Long workflows use), then passes the result through DaSiWa's Seamless Loop node, which picks the best loop point and morphs the end into the start with RIFE. It runs on the open ComfyUI, so ComfyUI must be running.

```
python -I tools/dasiwa_stitch.py "idle9_*_00001_.mp4" -o video/idle9_loop
python -I tools/dasiwa_stitch.py part1.mp4 part2.mp4 --no-loop
```

Clips can be full paths, or file names or globs in the output/video, output or input folder. Clips of a different size are scaled to the first clip's size, and the first clip's fps is used. `--overlap N` and `--mode` change the join, `--no-loop` only joins, `--rtx` uses RTX Frame Generation for the loop point, and `--dry-run` prints the graph. The script prints the saved file's path.

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
