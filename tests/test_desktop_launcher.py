"""Exercise the actual batch/pythonw launch chain and hidden-process diagnostics."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from tools.launch_editor import run_editor

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt', 'Windows desktop launcher')
class DesktopLauncherTests(unittest.TestCase):
    def setUp(self):
        folder = ROOT / '.local/test-launcher'
        folder.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='launch & Unicode Ω ', dir=folder)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        package = self.root / 'vayrshemon'
        package.mkdir()
        (package / '__init__.py').write_text('', encoding='utf-8')
        (package / '__main__.py').write_text('''
import ctypes, json, os, sys, time
from pathlib import Path
root = Path.cwd()
state = dict(console=ctypes.windll.kernel32.GetConsoleWindow(), argv=sys.argv[1:])
(root / 'started.json').write_text(json.dumps(state), encoding='utf-8')
print('Python stdout: Maxima Ω', flush=True)
print('Python stderr: transliteration ō', file=sys.stderr, flush=True)
os.write(1, b'Native stdout captured\\n')
os.write(2, b'Native stderr captured\\n')
if '--fail' in sys.argv:
    raise RuntimeError('deliberate startup failure')
if '--wait' in sys.argv:
    deadline = time.monotonic() + 15
    while not (root / 'finish').exists() and time.monotonic() < deadline:
        time.sleep(.05)
''', encoding='utf-8')

    def wait_for(self, predicate):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(.05)
        self.fail('Launcher did not finish the expected step within 10 seconds')

    def logs(self):
        return list((self.root / '.local/logs').glob('launch-*.log'))

    def test_batch_returns_while_editor_runs_without_console_and_keeps_output(self):
        # A minimal venv beside the copied launcher uses the real interpreter
        # with a fake editor, so no user document or workspace is touched.
        scripts = self.root / '.venv/Scripts'
        scripts.mkdir(parents=True)
        for name in ('python.exe', 'pythonw.exe'):
            shutil.copy2(Path(sys.executable).with_name(name), scripts / name)
        shutil.copy2(Path(sys.prefix) / 'pyvenv.cfg', scripts.parent / 'pyvenv.cfg')
        shutil.copy2(ROOT / 'launch.bat', self.root / 'launch.bat')
        (self.root / 'tools').mkdir()
        shutil.copy2(ROOT / 'tools/launch_editor.py', self.root / 'tools/launch_editor.py')
        document = self.root / 'My Maxima Ω & reading.vay'
        arguments = ['--document', str(document), '--m13', '--wait']
        try:
            command = subprocess.list2cmdline([str(self.root / 'launch.bat'), *arguments])
            # Measure the batch process, not EOF on pipes that a detached GUI
            # process can inherit from its parent.
            with (self.root / 'batch.log').open('wb') as output:
                result = subprocess.run(f'cmd.exe /d /s /c "{command}"',
                                        cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, timeout=10,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(result.returncode, 0, (self.root / 'batch.log').read_bytes())
            self.wait_for(lambda: (self.root / 'started.json').exists())
            self.assertEqual(len(self.logs()), 1)
            self.assertNotIn('EDITOR_EXIT_CODE', self.logs()[0].read_text(encoding='utf-8'))
        finally:
            (self.root / 'finish').touch()
            if self.logs():
                self.wait_for(lambda: 'EDITOR_EXIT_CODE=0' in self.logs()[0].read_text(encoding='utf-8'))
        state = json.loads((self.root / 'started.json').read_text(encoding='utf-8'))
        self.assertEqual(state['console'], 0)
        self.assertEqual(state['argv'], ['--root', str(self.root), 'editor', *arguments])
        log = self.logs()[0].read_text(encoding='utf-8')
        for text in ('Python stdout: Maxima Ω', 'Python stderr: transliteration ō',
                     'Native stdout captured', 'Native stderr captured'):
            self.assertIn(text, log)

    def test_pythonw_reports_child_failure_and_keeps_traceback(self):
        code = '''
from pathlib import Path
from unittest.mock import patch
from tools.launch_editor import run_editor
import sys
root = Path(sys.argv[1])
with patch('tools.launch_editor.report_error', lambda message: (root / 'error.txt').write_text(message, encoding='utf-8')):
    raise SystemExit(run_editor(root, ['--fail']))
'''
        result = subprocess.run([str(Path(sys.executable).with_name('pythonw.exe')), '-c', code, str(self.root)],
                                cwd=ROOT, timeout=20)
        self.assertEqual(result.returncode, 1)
        log = self.logs()[0]
        self.assertIn('RuntimeError: deliberate startup failure', log.read_text(encoding='utf-8'))
        self.assertIn('EDITOR_EXIT_CODE=1', log.read_text(encoding='utf-8'))
        self.assertIn(str(log), (self.root / 'error.txt').read_text(encoding='utf-8'))

    def test_unwritable_log_location_reports_startup_failure(self):
        (self.root / '.local').write_text('not a directory', encoding='utf-8')
        with patch('tools.launch_editor.report_error') as report:
            self.assertEqual(run_editor(self.root, []), 1)
        self.assertIn('could not start or create its log', report.call_args.args[0])
