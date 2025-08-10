"""
Display capture utilities for macOS using Quartz/AppKit.

- Enumerate physical displays
- Capture screenshots from a selected display

Note on Mission Control Spaces:
This captures the currently visible content of a physical display. Off-screen
Spaces (virtual desktops) cannot be captured until they are made visible on a
display by macOS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import io

import AppKit  # type: ignore
from Quartz import CoreGraphics as CG  # type: ignore
from PIL import Image  # type: ignore


@dataclass
class DisplayInfo:
    id: int
    index: int
    width: int
    height: int
    scale: float
    is_main: bool
    name: str


def _screen_to_display_info(screen: AppKit.NSScreen, index: int) -> DisplayInfo:
    desc = screen.deviceDescription()
    # NSScreenNumber is a CFNumber containing the CGDirectDisplayID
    display_id = int(desc.get("NSScreenNumber"))
    frame = screen.frame()
    width = int(frame.size.width)
    height = int(frame.size.height)
    scale = float(screen.backingScaleFactor()) if hasattr(screen, "backingScaleFactor") else 1.0
    is_main = bool(screen == AppKit.NSScreen.mainScreen())
    # Display names are not easily accessible without IOKit lookups; provide a friendly default
    name = f"Display {index}"
    return DisplayInfo(
        id=display_id,
        index=index,
        width=width,
        height=height,
        scale=scale,
        is_main=is_main,
        name=name,
    )


def list_displays() -> List[DisplayInfo]:
    screens = AppKit.NSScreen.screens() or []
    return [_screen_to_display_info(screen, idx) for idx, screen in enumerate(screens)]


def _cgimage_to_pil(cg_image) -> Image.Image:
    # Convert CGImage -> NSBitmapImageRep -> PNG bytes -> PIL Image
    rep = AppKit.NSBitmapImageRep.alloc().initWithCGImage_(cg_image)
    data = rep.representationUsingType_properties_(AppKit.NSPNGFileType, None)
    png_bytes = bytes(data)  # PyObjC exposes NSData as bytes-convertible
    return Image.open(io.BytesIO(png_bytes)).convert("RGB")


def grab_display(display_id: Optional[int]) -> Image.Image:
    if display_id is None:
        # Fallback: capture main display
        main = AppKit.NSScreen.mainScreen()
        if main is None:
            raise RuntimeError("No main screen available for capture")
        desc = main.deviceDescription()
        display_id = int(desc.get("NSScreenNumber"))

    cg_img = CG.CGDisplayCreateImage(display_id)
    if cg_img is None:
        raise RuntimeError(f"Failed to capture display id {display_id}")
    return _cgimage_to_pil(cg_img)


class ScreenshotProvider:
    """Provides screenshots from a selected macOS display via Quartz."""

    def __init__(self, display_index: Optional[int] = None):
        self._displays: List[DisplayInfo] = list_displays()
        self._selected: Optional[DisplayInfo] = None
        if display_index is not None:
            self.select_display_by_index(display_index)

    def refresh(self) -> None:
        self._displays = list_displays()

    def list_display_infos(self) -> List[DisplayInfo]:
        self.refresh()
        return list(self._displays)

    def select_display_by_index(self, index: int) -> DisplayInfo:
        self.refresh()
        if index < 0 or index >= len(self._displays):
            raise IndexError(f"Display index {index} out of range (found {len(self._displays)})")
        self._selected = self._displays[index]
        return self._selected

    def current_display(self) -> Optional[DisplayInfo]:
        return self._selected

    def screenshot(self) -> Image.Image:
        display_id = self._selected.id if self._selected else None
        return grab_display(display_id)


