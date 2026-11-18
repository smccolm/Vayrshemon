"""Scalable, individually accessible keys cut from the author's keyboard artwork."""
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QBitmap, QColor, QFont, QImage, QPainter, QPixmap, QRegion
from PySide6.QtWidgets import QAbstractButton, QWidget
from .keyboard_layout import native_keys


class ArtKey(QAbstractButton):
    def __init__(self, board, index, mask):
        super().__init__(board)
        self.board = board
        self.index = index
        y, x = np.nonzero(mask)
        self.source = QRect(int(x.min()), int(y.min()), int(x.max()-x.min()+1), int(y.max()-y.min()+1))
        cut = mask[self.source.top():self.source.bottom()+1, self.source.left():self.source.right()+1]
        # Bitmap masks have an opaque bit for black, a transparent bit for white.
        pixels = np.ascontiguousarray(np.where(cut, 0, 255), dtype=np.uint8)
        self.stencil = QImage(pixels.data, pixels.shape[1], pixels.shape[0], pixels.strides[0],
                              QImage.Format.Format_Grayscale8).copy()
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName(board.keys[index].name)
        self.clicked.connect(lambda: board.activate(index))

    def resizeEvent(self, event):
        image = self.stencil.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio,
                                    Qt.TransformationMode.FastTransformation)
        self.setMask(QRegion(QBitmap.fromImage(image, Qt.ImageConversionFlag.MonoOnly)))

    def paintEvent(self, event):
        board = self.board
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        key = board.keys[self.index]
        if self.isDown() and not board.roman:
            painter.drawPixmap(self.rect(), board.down[board.upper], self.source)
        if board.roman and not key.command and key.lower != ' ':
            value = key.upper if board.upper else key.lower
            family = board.roman_face.family if ord(value) in board.roman_face.cmap else 'Segoe UI'
            font = QFont(family)
            font.setPixelSize(max(12, round(self.height() * .48)))
            painter.setFont(font)
            painter.setPen(QColor('#effbff'))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, value)
        if (self.isDown() and board.roman) or (key.name == 'Caps' and board.caps):
            painter.fillRect(self.rect(), QColor(104, 203, 235, 65))


class NativeBoard(QWidget):
    def __init__(self, root, roman_face, activate):
        super().__init__()
        self.keys = native_keys(root)
        self.activate = activate
        self.roman_face = roman_face
        self.upper = self.roman = self.caps = False
        directory = root / 'data/keyboard'
        self.art = [QPixmap(str(directory / name)) for name in ('minima.png', 'maxima.png', 'roman-keys.png')]
        self.down = [QPixmap(str(directory / name)) for name in ('minima-down.png', 'maxima-down.png')]
        with Image.open(directory / 'hit-map.png') as image:
            mask = np.asarray(image.convert('RGBA'))
        self.art_size = QSize(mask.shape[1], mask.shape[0])
        if any(p.size() != self.art_size for p in self.art + self.down):
            raise ValueError('Keyboard artwork dimensions do not match the hit map.')
        self.buttons = []
        for i in range(len(self.keys)):
            region = (mask[:, :, 0] == 252 - 3*i) & (mask[:, :, 3] == 255)
            self.buttons.append(ArtKey(self, i, region))
        self.setMinimumSize(400, 145)

    def bounds(self):
        size = self.art_size.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        rect = QRect(0, 0, size.width(), size.height())
        rect.moveCenter(self.rect().center())
        return rect

    def resizeEvent(self, event):
        area = self.bounds()
        sx, sy = area.width()/self.art_size.width(), area.height()/self.art_size.height()
        for button in self.buttons:
            r = button.source
            x, y = round(r.x()*sx), round(r.y()*sy)
            button.setGeometry(area.left()+x, area.top()+y,
                               round((r.right()+1)*sx)-x, round((r.bottom()+1)*sy)-y)

    def set_layer(self, roman, upper, caps):
        self.roman, self.upper, self.caps = roman, upper, caps
        for button, key in zip(self.buttons, self.keys):
            value = key.upper if upper else key.lower
            label = key.name if key.command or value == ' ' else f'{key.name} · U+{ord(value):04X}'
            button.setToolTip(label)
            button.update()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(self.bounds(), self.art[2 if self.roman else int(self.upper)])
