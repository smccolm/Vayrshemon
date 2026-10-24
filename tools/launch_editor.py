"""Windowless desktop launcher; retain Python and native output in a launch log."""
from datetime import datetime
from pathlib import Path
import os
import subprocess
import sys
import traceback


def report_error(message):
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, message, 'Vayrshemon', 0x10)


def run_editor(root, arguments):
    root = Path(root).resolve()
    log = root / '.local/logs' / (
        'launch-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + f'-{os.getpid()}.log')
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('xb', buffering=0) as output:
            try:
                # Redirect at the process boundary so early Qt/native messages,
                # Python tracebacks and structured diagnostics all reach disk.
                command = [str(Path(sys.executable).with_name('python.exe')),
                           '-u', '-X', 'utf8', '-X', 'faulthandler', '-m', 'vayrshemon',
                           '--root', str(root), 'editor', *arguments]
                result = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL,
                                        stdout=output, stderr=subprocess.STDOUT,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                code = result.returncode
                output.write(f'\nEDITOR_EXIT_CODE={code}\n'.encode('utf-8'))
            except Exception:
                output.write(traceback.format_exc().encode('utf-8'))
                code = 1
    except Exception as error:
        report_error('The editor could not start or create its log.\n\n' + str(error))
        return 1
    if code:
        report_error('The editor stopped with an error.\n\nDetails: ' + str(log))
    return code


if __name__ == '__main__':
    raise SystemExit(run_editor(Path(__file__).resolve().parents[1], sys.argv[1:]))
