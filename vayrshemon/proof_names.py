"""Local-time filename suggestions only; exporting still requires a chosen path."""
from datetime import datetime
import re


def suggested_proof_path(session, extension):
    title=re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', session.state['title']).strip(' .')[:80] or 'page'
    when=datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')[:-3]
    return str(session.root/'.local'/f'{title}_{when}.{extension}')
