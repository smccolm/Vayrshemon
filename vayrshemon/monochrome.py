"""Presentation-only black/white palette shared by screen and proof painters."""
from PySide6.QtGui import QColor


def palette(background='#FFFFFFFF'):
    """Keep dark paper dark, with opposite opaque ink; transparency is white paper.

    Compare perceived brightness after compositing the source over white. Only
    painting uses this palette: saved colors, glyphs and layout remain untouched.
    Raster antialiasing may introduce neutral grays at glyph edges.
    """
    color=QColor(background)
    brightness=.2126*color.redF()+.7152*color.greenF()+.0722*color.blueF()
    brightness=color.alphaF()*brightness+(1-color.alphaF())
    dark=brightness<.5
    return QColor('black' if dark else 'white'),QColor('white' if dark else 'black')
