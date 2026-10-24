"""Create a separate, source-bound four-column proof from an existing facing book."""
import argparse
import json
import uuid
from pathlib import Path
from PySide6.QtWidgets import QApplication
from vayrshemon.forge import ForgeProject
from vayrshemon.gloss_api import GlossSession,GlossAPI


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('document','project','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--version',required=True);p.add_argument('--test',required=True)
    args=p.parse_args();app=QApplication.instance() or QApplication([])
    root=Path(__file__).resolve().parents[1];s=GlossSession(root,source_fonts=False,recovery=False)
    try:
        s.open(args.document,advance_revision=False);s.forge=ForgeProject(args.project)
        r=GlossAPI(s).call('page.gloss.copy',dict(version=args.version,test_id=args.test,directory=str(args.out.resolve())),expected_revision=s.revision,idempotency_key=uuid.uuid4().hex)
        print(json.dumps(r,ensure_ascii=True,indent=2));return 0 if r['ok'] else 1
    finally:s.finish()


if __name__=='__main__':raise SystemExit(main())
