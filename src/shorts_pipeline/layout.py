"""Vertical 9:16 layouts as ffmpeg filter graphs (1080x1920).

Three framings, picked per clip:

* ``stacked``      webcam on top (40 %), gameplay below (60 %).
* ``stacked_wide`` same, but when the gameplay crop is wide (a menu or a console
                   screen where the joke lives) it is shown *whole* over a
                   blurred copy of itself instead of being cropped to portrait.
* ``full``         the whole frame centred over a blurred, darkened copy. Used when
                   the streamer's camera already fills the screen, so we never
                   duplicate the face above and below.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Mode = Literal["stacked", "full"]
W, H = 1080, 1920
CAM_H = 768                 # 40 % of 1920
GAME_H = H - CAM_H          # 1152


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int

    def crop(self) -> str:
        return f"crop={self.w}:{self.h}:{self.x}:{self.y}"


_BLUR = "scale=135:144,gblur=sigma=5,scale=1080:1152:flags=bicubic,eq=brightness=-0.12"


def filtergraph(mode: Mode, cam: Box | None = None, game: Box | None = None,
                *, fast: bool = False) -> str:
    """Return a ``-filter_complex`` string whose output pad is ``[base]``."""
    flags = "bilinear" if fast else "lanczos"
    if mode == "full":
        return (
            "[0:v]fps=30,split[a][b];"
            f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            "scale=135:240,gblur=sigma=5,"
            f"scale={W}:{H}:flags=bicubic,eq=brightness=-0.12[bg];"
            f"[b]scale={W}:-2:flags={flags}[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[base]"
        )
    if mode != "stacked":
        raise ValueError(f"unknown framing mode: {mode!r}")
    if cam is None or game is None:
        raise ValueError("stacked mode needs both a cam box and a game box")

    if game.w > 1.2 * game.h:  # wide crop: show whole, over a blurred backdrop
        return (
            "[0:v]fps=30,split=3[a][b][c];"
            f"[a]{cam.crop()},scale={W}:{CAM_H}:flags={flags}[cam];"
            f"[b]{game.crop()},scale={W}:{GAME_H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{GAME_H},{_BLUR}[bg];"
            f"[c]{game.crop()},scale={W}:-2:flags={flags}[fg];"
            "[bg][fg]overlay=0:(H-h)/2[game];"
            "[cam][game]vstack[base]"
        )
    return (
        "[0:v]fps=30,split[a][b];"
        f"[a]{cam.crop()},scale={W}:{CAM_H}:flags={flags}[cam];"
        f"[b]{game.crop()},scale={W}:{GAME_H}:flags={flags}[game];"
        "[cam][game]vstack[base]"
    )


def ffmpeg_command(src: str, start: float, end: float, dst: str, graph: str,
                   *, crf: int = 20) -> list[str]:
    """Cut [start, end] from ``src`` and render it with the given layout."""
    return [
        "ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
        "-i", src, "-filter_complex", graph + ";[base]format=yuv420p[v]",
        "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "medium",
        "-crf", str(crf), "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", dst,
    ]
