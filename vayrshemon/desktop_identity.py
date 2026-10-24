"""Give Windows a stable taskbar identity before creating any Qt windows."""
import ctypes
import sys
from pathlib import Path

APP_ID = 'Vayrshemon.LanguageWorkbench'


def create_application(root):
    if sys.platform == 'win32':
        shell = ctypes.WinDLL('shell32', use_last_error=True)
        identify = shell.SetCurrentProcessExplicitAppUserModelID
        identify.argtypes = [ctypes.c_wchar_p]
        identify.restype = ctypes.c_long
        result = identify(APP_ID)
        if result < 0:
            raise OSError(f'TASKBAR_IDENTITY_FAILED: HRESULT 0x{result & 0xffffffff:08X}')
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    app.setApplicationName('Vayrshemon')
    icon = QIcon(str(Path(root) / 'data/icons/memon-color.ico'))
    if icon.isNull():
        raise ValueError('APPLICATION_ICON_MISSING: data/icons/memon-color.ico')
    app.setWindowIcon(icon)
    return app
