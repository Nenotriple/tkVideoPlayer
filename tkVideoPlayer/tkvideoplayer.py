#region Imports


# Standard Library
import gc
import time
import logging
import threading

# Standard Library - GUI
import tkinter as tk

# Third-Party Libraries
import av
from PIL import Image, ImageOps, ImageTk

# Type Hinting
from typing import Dict, Tuple, Optional, Any

# Suppress libav logging
logging.getLogger('libav').setLevel(logging.ERROR)


#endregion
#region TkinterVideo


class TkinterVideo(tk.Label):
    """Tkinter label widget for video playback.
    Supports scaling, aspect ratio, frame rate consistency, and seeking.
    """
    def __init__(
        self,
        master: Any,
        scaled: bool = True,
        consistent_frame_rate: bool = True,
        keep_aspect: bool = False,
        *args: Any,
        **kwargs: Any
    ) -> None:
        super(TkinterVideo, self).__init__(master, *args, **kwargs)

        self.video_path = ""
        self._video_load_thread = None

        self._is_paused = True
        self._should_stop = True

        # Skip frames to maintain frame rate if decoding is slow
        self.consistent_frame_rate = consistent_frame_rate

        self._video_container = None

        self._current_frame_image = None
        self._current_frame_tk = None
        self._current_frame_number = 0
        self._current_timestamp = 0

        self._current_display_size = (0, 0)

        self._should_seek = False
        self._seek_seconds = 0

        self._video_info = {
            "duration": 0,
            "framerate": 0,
            "framesize": (0, 0)  # (width, height)
        }

        self.set_scaled(scaled)
        self._keep_aspect_ratio = keep_aspect
        self._resampling_method: int = Image.NEAREST

        self.bind("<<Destroy>>", self.stop)
        self.bind("<<FrameGenerated>>", self._display_frame)


#endregion
#region Load/Play/Pause/Stop


    def load(self, video_file_path: str) -> None:
        """Load video file from path."""
        self.stop()
        self.video_path = video_file_path


    def play(self) -> None:
        """Start video playback."""
        self._is_paused = False
        self._should_stop = False
        if not self._video_load_thread:
            self._video_load_thread = threading.Thread(target=self._load, args=(self.video_path,), daemon=True)
            self._video_load_thread.start()


    def pause(self) -> None:
        """Pause video playback."""
        self._is_paused = True


    def stop(self, *args: Any, **kwargs: Any) -> None:
        """Stop video playback and cleanup."""
        self._is_paused = True
        self._should_stop = True
        self._cleanup()


    def seek(self, seconds: float, precise: bool = False) -> None:
        """Seek to a specific time.
        If precise is True and paused, waits briefly for accuracy.
        """
        self._should_seek = True
        self._seek_seconds = seconds
        if precise and self._is_paused:
            time.sleep(0.01)


#endregion
#region Info & Metadata


    def video_info(self) -> Dict[str, Any]:
        """Return video info: duration, framerate, framesize."""
        return self._video_info


    def metadata(self) -> Dict[str, Any]:
        """Return video metadata if available."""
        if self._video_container:
            return self._video_container.metadata
        return {}


    def current_frame_number(self) -> int:
        """Return current frame number."""
        return self._current_frame_number


    def current_duration(self) -> float:
        """Return current playback time in seconds."""
        return self._current_timestamp


    def current_img(self) -> Optional[Image.Image]:
        """Return current frame image."""
        return self._current_frame_image


    def is_paused(self) -> bool:
        """Return True if video is paused."""
        return self._is_paused


#endregion
#region Aspect Ratio & Resampling


    def keep_aspect(self, keep_aspect_ratio: bool) -> None:
        """Set aspect ratio preservation on resize."""
        self._keep_aspect_ratio = keep_aspect_ratio


    def set_resampling_method(self, resampling_method: int) -> None:
        """Set image resampling method for resizing."""
        self._resampling_method = resampling_method


    def set_size(self, display_size: Tuple[int, int], keep_aspect_ratio: bool = False) -> None:
        """Set video display size."""
        self.set_scaled(False, self._keep_aspect_ratio)
        self._current_display_size = display_size
        self._keep_aspect_ratio = keep_aspect_ratio


    def set_scaled(self, scaled: bool, keep_aspect_ratio: bool = False) -> None:
        """Enable or disable scaling and aspect ratio."""
        self.scaled = scaled
        self._keep_aspect_ratio = keep_aspect_ratio
        if scaled:
            self.bind("<Configure>", self._resize_event)
        else:
            self.unbind("<Configure>")
            self._current_display_size = self.video_info()["framesize"]


#endregion
#region Resize Event


    def _resize_event(self, event: tk.Event) -> None:
        self._current_display_size = event.width, event.height
        if self._is_paused and self._current_frame_image and self.scaled:
            if self._keep_aspect_ratio:
                resized_image = ImageOps.contain(self._current_frame_image.copy(), self._current_display_size)
            else:
                resized_image = self._current_frame_image.copy().resize(self._current_display_size)
            photo_image = self._create_photoimage(resized_image)
            self._safe_config_image(photo_image)


    def _set_frame_size(self, _event: Optional[Any] = None) -> None:
        """Set frame size for display."""
        if not self.winfo_exists():
            return
        intrinsic_size = (
            self._video_container.streams.video[0].width,
            self._video_container.streams.video[0].height,
        )
        self._video_info["framesize"] = intrinsic_size
        if self._current_display_size == (0, 0):
            self._current_display_size = intrinsic_size
        if self._current_frame_image is None:
            blank_image = Image.new("RGBA", intrinsic_size, (255, 0, 0, 0))
            self._current_frame_image = blank_image
            photo_image = self._create_photoimage(blank_image)
            if photo_image is not None:
                self._safe_config_image(photo_image)
                def safe_configure():
                    if self.winfo_exists():
                        try:
                            self.config(width=150, height=100)
                        except tk.TclError:
                            pass
                self.after(0, safe_configure)


#endregion
#region Display Frame


    def _display_frame(self, _event: Optional[Any]) -> None:
        """Update label with current frame image."""
        try:
            existing_photoimage = getattr(self, "_current_imgtk", None)
            if existing_photoimage and existing_photoimage.width() == self._current_frame_image.width and existing_photoimage.height() == self._current_frame_image.height:
                try:
                    existing_photoimage.paste(self._current_frame_image)
                    self._safe_config_image(existing_photoimage)
                    return
                except Exception:
                    pass
            photo_image = self._create_photoimage(self._current_frame_image)
            self._safe_config_image(photo_image)
        except AttributeError:
            pass


#endregion
#region Load Thread


    def _load(self, video_file_path: str) -> None:
        """Load and decode video frames in a separate thread.
        Handles seeking, frame display, and frame rate consistency.
        """
        current_thread = threading.current_thread()
        try:
            with av.open(video_file_path) as self._video_container:
                self._video_container.streams.video[0].thread_type = "AUTO"
                self._video_container.fast_seek = False
                self._video_container.discard_corrupt = True
                video_stream = self._video_container.streams.video[0]
                try:
                    self._video_info["framerate"] = int(video_stream.average_rate)
                except TypeError:
                    raise TypeError("Not a video file")
                try:
                    self._video_info["duration"] = float(video_stream.duration * video_stream.time_base)
                    self._safe_generate_event("<<Duration>>")
                except (TypeError, tk.TclError):
                    pass
                self._current_frame_number = 0
                self._set_frame_size()
                self.stream_base = video_stream.time_base
                self._safe_generate_event("<<Loaded>>")
                current_time_ms = self._get_time_in_ms()
                previous_time_ms = current_time_ms
                time_per_frame_ms = (1 / self._video_info["framerate"]) * 1000
                while self._video_load_thread == current_thread and not self._should_stop:
                    if self._should_seek:
                        seek_time_us = int(self._seek_seconds * 1000000)
                        target_pts = self._seek_seconds / video_stream.time_base
                        self._seek_and_decode_to_target_pts(seek_time_us, target_pts, video_stream)
                        self._should_seek = False
                        self._seek_seconds = 0
                    if self._is_paused:
                        time.sleep(0.0001)
                        continue
                    current_time_ms = self._get_time_in_ms()
                    delta_ms = current_time_ms - previous_time_ms
                    previous_time_ms = current_time_ms
                    try:
                        frame = next(self._video_container.decode(video=0))
                        self._process_frame(frame)
                        if self.consistent_frame_rate:
                            time.sleep(max((time_per_frame_ms - delta_ms) / 1000, 0))
                    except (StopIteration, av.error.EOFError, tk.TclError):
                        break
            self._close_container()
        finally:
            self._cleanup()
            gc.collect()


    def _seek_and_decode_to_target_pts(self, seek_time_us: int, target_pts: float, video_stream: Any) -> None:
        """Seek and decode frames until reaching the target PTS."""
        self._video_container.seek(seek_time_us, whence='time', backward=True, any_frame=False)
        for frame in self._video_container.decode(video=0):
            if frame.pts >= target_pts:
                self._update_current_frame_data(frame)
                self._safe_generate_event("<<FrameGenerated>>")
                break


    # --- Frame Processing ---
    def _process_frame(self, frame: Any) -> None:
        """Update frame, timestamp, frame number, and generate frame event."""
        self._update_current_frame(frame)
        if self._current_frame_number % self._video_info["framerate"] == 0:
            self._safe_generate_event("<<SecondChanged>>")


    def _update_current_frame(self, frame: Any) -> None:
        """Update current frame image, timestamp, frame number, and generate frame event."""
        self._update_current_frame_data(frame)
        self._safe_generate_event("<<FrameGenerated>>")


    def _update_current_frame_data(self, frame: Any) -> None:
        """Update current frame image, timestamp, and frame number."""
        self._current_timestamp = float(frame.pts * self._video_container.streams.video[0].time_base)
        self._current_frame_number = int(self._video_info["framerate"] * self._current_timestamp)
        width, height = self._get_resized_dimensions(frame, self._current_display_size)
        self._current_frame_image = frame.to_image(width=width, height=height, interpolation="FAST_BILINEAR")


    # --- Frame/Image Utilities ---
    def _get_resized_dimensions(self, frame: Any, target_display_size: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate resized dimensions according to aspect ratio settings."""
        width, height = target_display_size
        if self._keep_aspect_ratio:
            image_ratio = frame.width / frame.height
            destination_ratio = width / height
            if image_ratio != destination_ratio:
                if image_ratio > destination_ratio:
                    new_height = round(frame.height / frame.width * width)
                    height = new_height
                else:
                    new_width = round(frame.width / frame.height * height)
                    width = new_width
        return width, height


    def _create_photoimage(self, pil_image: Image.Image) -> Optional[ImageTk.PhotoImage]:
        """Create an ImageTk.PhotoImage safely (returns None on widget destruction)."""
        try:
            return ImageTk.PhotoImage(pil_image)
        except tk.TclError:
            return None


    def _safe_config_image(self, photoimage: Optional[ImageTk.PhotoImage]) -> None:
        """Apply a PhotoImage to the label on the main thread if possible."""
        if photoimage is None:
            return
        try:
            # Schedule UI update on main thread to avoid Tk issues from worker thread
            def safe_configure():
                if self.winfo_exists():
                    try:
                        self.config(image=photoimage)
                    except tk.TclError:
                        pass
            self.after(0, safe_configure)
            # keep a reference so it's not garbage collected
            self._current_imgtk = photoimage
        except tk.TclError:
            pass


    # --- Event Utilities ---
    def _safe_generate_event(self, event_name: str) -> None:
        """Generate a tkinter event safely (ignore TclError when widget destroyed)."""
        try:
            self.event_generate(event_name)
        except tk.TclError:
            pass


    # --- Container & Cleanup ---
    def _close_container(self) -> None:
        """Safely close the av container and clear the reference."""
        if self._video_container:
            try:
                self._video_container.close()
            except Exception:
                pass
            self._video_container = None


    def _cleanup(self) -> None:
        self._current_frame_number = 0
        self._is_paused = True
        self._should_stop = True
        if self._video_load_thread:
            self._video_load_thread = None
        self._close_container()
        self._safe_generate_event("<<Ended>>")


    # --- Misc Utilities ---
    def _get_time_in_ms(self) -> int:
        """Return current time in milliseconds."""
        return time.time_ns() // 1_000_000


#endregion
