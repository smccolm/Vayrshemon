"""Check Windows' real process identity and Qt's inherited application icon."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DesktopIdentityTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'win32', 'Windows taskbar identity')
    def test_native_identity_and_memon_icon_in_fresh_process(self):
        # A separate process checks actual Windows state without changing the
        # test runner's identity or relying on a previously created QApplication.
        code = '''
import ctypes
from pathlib import Path
from vayrshemon.desktop_identity import APP_ID, create_application
app = create_application(Path.cwd())
shell = ctypes.WinDLL('shell32')
get_id = shell.GetCurrentProcessExplicitAppUserModelID
get_id.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
get_id.restype = ctypes.c_long
value = ctypes.c_void_p()
assert get_id(ctypes.byref(value)) == 0
try:
    assert ctypes.wstring_at(value) == APP_ID
finally:
    free = ctypes.WinDLL('ole32').CoTaskMemFree
    free.argtypes = [ctypes.c_void_p]
    free.restype = None
    free(value)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget
expected = QIcon('data/icons/memon-color.ico')
window = QWidget()
for size in (16, 24, 32, 48, 256):
    assert app.windowIcon().pixmap(size, size).toImage() == expected.pixmap(size, size).toImage()
    assert window.windowIcon().pixmap(size, size).toImage() == expected.pixmap(size, size).toImage()
assert app.applicationName() == 'Vayrshemon'
print(APP_ID + ': native identity and all Memon icon sizes verified')
'''
        result = subprocess.run([sys.executable, '-c', code], cwd=ROOT,
                                env=dict(os.environ, QT_QPA_PLATFORM='windows'),
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('all Memon icon sizes verified', result.stdout)
