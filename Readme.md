# tkVideoPlayer

A simple library for playing video files in Tkinter. Features include play, pause, skip, and seeking to specific timestamps.

## Example usage

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

- [Read the documentation](https://github.com/PaulleDemon/tkVideoPlayer/blob/master/Documentation.md)
- [How to integrate with CustomTkinter?](https://github.com/PaulleDemon/tkVideoPlayer/discussions/23#discussioncomment-4475005)

## Sample video player

![Sample player screenshot](https://github.com/PaulleDemon/tkVideoPlayer/blob/master/videoplayer_screenshot.png?raw=True)

> **Note:** The above is a video player made using this library. The UI is not included.
> See the [example on building the video player](https://github.com/PaulleDemon/tkVideoPlayer/blob/master/examples/sample_player.py).

## Related libraries

- [tkstylesheet](https://pypi.org/project/tkstylesheet/) — Style your Tkinter application using stylesheets.
- [tkTimePicker](https://pypi.org/project/tkTimePicker/) — An easy-to-use time picker.
- [PyCollision](https://pypi.org/project/PyCollision/) — Draw hitboxes for 2D games.
