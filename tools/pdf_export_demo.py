"""Create six review PDFs through the real menu/worker, preserving the source save."""
import argparse
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import shutil,subprocess,time,uuid
from unittest.mock import patch
from pypdf import PdfReader
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from tools.m0.common import file_hash,write_json
from tools.approved_baseline import protected_state,content_hash
from vayrshemon.file_api import FileSession,FileAPI
from vayrshemon.file_window import FileWindow


def run(source,out,dpi=300):
    project=Path(__file__).resolve().parents[1];source=Path(source).resolve();out=Path(out).resolve()
    stamp=datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')[:-3]
    work=project/'.local/pdf-export-review'/stamp
    shutil.copytree(project/'schemas',work/'schemas');shutil.copytree(project/'data',work/'data')
    out.mkdir(parents=True,exist_ok=True);source_hash=file_hash(source)
    app=QApplication.instance() or QApplication([])
    book=FileSession(work,source_fonts=False,recovery=False);book.open(source,advance_revision=False)
    api=FileAPI(book);window=FileWindow(book,api);window.proof_dpi.setValue(dpi)
    protected=protected_state(book.capture());original_pages=deepcopy(book.capture()['pages']);results=[]
    try:
        for view,label in (('one','Single'),('two','Double')):
            for mode,paper,treatment in (('mono','white','Black-on-white'),('mono','black','White-on-black'),('color','black','Color')):
                result=api.call('view.configure',dict(mode=mode,monochromePaper=paper),expected_revision=book.revision,idempotency_key=uuid.uuid4().hex)
                assert result['ok'],result
                window.page_controls.set_mode(view,persist=False)
                before=book.capture();path=out/f'{stamp}_{label}_{treatment}.pdf'
                with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(str(path),'PDF (*.pdf)')):
                    window.pdf_export_action.trigger()
                jobs=book.jobs.status()['jobs'];assert jobs,window.last_error
                job=jobs[-1];deadline=time.monotonic()+240
                while job['status']=='running' and time.monotonic()<deadline:
                    QTest.qWait(100);job=book.jobs.status(job['jobId'])
                assert job['status']=='completed',job
                assert book.capture()==before
                assert protected_state(book.capture())==protected
                assert book.capture()['pages']==original_pages
                reader=PdfReader(path)
                assert len(reader.pages)==len(original_pages)
                assert reader.page_labels==[str(i+1) for i in range(len(original_pages))]
                assert reader.page_layout==('/SinglePage' if view=='one' else '/TwoPageLeft')
                assert reader.get_destination_page_number(reader.open_destination)==0
                for actual,expected in zip(reader.pages,original_pages):
                    assert abs(float(actual.mediabox.width)-int(expected['width'])/1e6)<.000001
                    assert abs(float(actual.mediabox.height)-int(expected['height'])/1e6)<.000001
                # Rendering streams must match between the single and double view exports.
                streams=[content_hash(p.get_contents().get_data().hex()) for p in reader.pages]
                if view=='two':assert streams==next(r['contentStreams'] for r in results if r['treatment']==treatment)
                prefix=work/f'{label}_{treatment}'
                subprocess.run(['pdftoppm','-r','96','-png',str(path),str(prefix)],check=True,capture_output=True)
                images=sorted(work.glob(prefix.name+'-*.png'))
                entry=dict(path=str(path),view=view,treatment=treatment,pages=len(reader.pages),pageLabels=reader.page_labels,
                    pageLayout=reader.page_layout,points=[[float(p.mediabox.width),float(p.mediabox.height)] for p in reader.pages],
                    expectedPoints=[[int(p[k])/1e6 for k in ('width','height')] for p in original_pages],
                    pngs=[str(p) for p in images],contentStreams=streams,job=job,sha256=file_hash(path))
                results.append(entry);write_json(work/'results.json',dict(source=str(source),sourceSha256=source_hash,results=results))
                print('REVIEW_PDF_READY '+str(path),flush=True)
        assert file_hash(source)==source_hash
        print('REVIEW_REPORT '+str(work/'results.json'),flush=True)
        return work/'results.json'
    finally:
        window.job_timer.stop();window.forge_panel.timer.stop();window.timer.stop();window.hide()
        book.window=None;book._editor=None;window.deleteLater();book.finish()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--dpi',type=int,default=300)
    args=parser.parse_args();run(args.source,args.out,args.dpi)
