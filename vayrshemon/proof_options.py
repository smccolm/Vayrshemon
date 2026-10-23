"""Choose the highest supported whole-number DPI for a desktop proof."""
import math
from .layout import MAX_PIXELS


def supported_dpi(area,requested):
    for dpi in range(min(600,requested),71,-1):
        width=math.ceil(area.width()*dpi/96);height=math.ceil(area.height()*dpi/96)
        if max(width,height)<=32767 and width*height<=MAX_PIXELS: return dpi
    raise ValueError('Page is too large for a whole-page PNG at 72 DPI. Export a bounded region through render.png or reduce the page size.')
