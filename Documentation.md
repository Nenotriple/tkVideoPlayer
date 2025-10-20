# tkVideoPlayer Documentation

## Installation

```shell
pip install tkvideoplayer
```

## Quickstart

```python
import tkinter as tk
from tkVideoPlayer import TkinterVideo

root = tk.Tk()

videoplayer = TkinterVideo(master=root, scaled=True)
videoplayer.load(r"samplevideo.mp4")
videoplayer.pack(expand=True, fill="both")

videoplayer.play()  # play the video

root.mainloop()
```

[See additional examples](https://github.com/Nenotriple/tkVideoPlayer/tree/master/examples)

## Methods

TkVideoPlayer inherits from `tk.Label` and displays the image on the label.

Below are the available methods:

| Method                  | Parameters                                                                                              | Description                                                                                                                     |
|-------------------------|---------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `__init__`              | `scaled` (bool), `consistent_frame_rate` (bool, default `True`), `keep_aspect` (bool, default `False`)  | Resizes video to fit label. Skips frames to maintain framerate. Preserves aspect ratio (won't upscale) if `keep_aspect` is set. |
| `set_scaled`            | `scaled` (bool), `keep_aspect` (bool, default `False`)                                                  | Scales the video to the label size.                                                                                             |
| `load`                  | `file_path` (str)                                                                                       | Loads the video in a thread.                                                                                                    |
| `set_size`              | `size` (Tuple[int, int]), `keep_aspect` (bool, default `False`)                                         | Sets the video frame size. Setting this disables scaling.                                                                       |
| `current_duration`      | -                                                                                                       | Returns video duration in seconds.                                                                                              |
| `video_info`            | -                                                                                                       | Returns a dictionary with framerate, framesize, and duration.                                                                   |
| `play`                  | -                                                                                                       | Plays the video.                                                                                                                |
| `pause`                 | -                                                                                                       | Pauses the video.                                                                                                               |
| `is_paused`             | -                                                                                                       | Returns whether the video is currently paused.                                                                                  |
| `stop`                  | -                                                                                                       | Stops playback and closes the file.                                                                                             |
| `seek`                  | `sec` (int)                                                                                             | Moves to a specific timestamp (in seconds).                                                                                     |
| `keep_aspect`           | `keep_aspect` (bool)                                                                                    | Keeps aspect ratio when resizing.                                                                                               |
| `metadata`              | -                                                                                                       | Returns meta information as a dictionary, if available.                                                                         |
| `set_resampling_method` | `method` (int)                                                                                          | Sets resizing method. Defaults to NEAREST. See PIL docs for details.                                                            |

## Virtual Events

These events can be bound for custom behavior:

| Virtual Event        | Description                                                                         |
|----------------------|-------------------------------------------------------------------------------------|
| `<<Loaded>>`         | Generated when the video file is opened.                                            |
| `<<Duration>>`       | Generated when the video duration is found.                                         |
| `<<SecondChanged>>`  | Generated whenever a second passes in the video (`frame_number % frame_rate == 0`). |
| `<<FrameGenerated>>` | Generated whenever a new frame is available. (Internal use; bind only if needed.)   |
| `<<Ended>>`          | Generated when the video has ended.                                                 |

> **Note:**
> To draw on the video, fork the repo and inherit from `Canvas` instead of `Label`.
> Use `image_id = self.create_image()` and update the image using `image_id`.
