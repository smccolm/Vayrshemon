"""Export every physical page in one PDF using the current reading arrangement."""
from pathlib import Path
from PySide6.QtWidgets import QFileDialog,QMessageBox
from tools.m0.common import file_hash
from .proof_names import suggested_proof_path
from .proof_options import supported_dpi
from .pages import page_rect


def export_document(window):
    book=window.book;requested=int(window.proof_dpi.value());dpi=requested
    # Outline-only PDF has no whole-page raster allocation limit.
    if book.view['mode']=='color' and any(b['enabled'] for b in book.state['paint']['bindings']):
        try:dpi=min(supported_dpi(page_rect(p),requested) for p in book.state['pages'])
        except ValueError as error:window.statusBar().showMessage(str(error),30000);return
    path,_=QFileDialog.getSaveFileName(window,f'Export PDF · all {len(book.state["pages"])} pages · {dpi} DPI',
        suggested_proof_path(book,'pdf'),'PDF (*.pdf)',options=QFileDialog.Option.DontConfirmOverwrite)
    if not path:return
    if not path.lower().endswith('.pdf'):path+='.pdf'
    target=Path(path);replace={}
    if target.exists():
        if not target.is_file():window.statusBar().showMessage('Export path must be a file: '+path,30000);return
        previous=file_hash(target)
        if QMessageBox.question(window,'Replace PDF?',path+' already exists. Replace it when the complete PDF is ready?',
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        replace['replace_sha256']=previous
    result=window.invoke('jobs.export',path=path,format='pdf',mode=book.view['mode'],dpi=dpi,raster_policy='raster',
        pdf_view=window.preview.page_mode,**replace)
    if result:
        window.poll_jobs()
        window.statusBar().showMessage(f'Exporting all {len(book.state["pages"])} pages to PDF · {dpi} DPI · '+path,30000)
        book.log.emit('publication','DESKTOP_PDF_REQUESTED',requestedDpi=requested,actualDpi=dpi,path=path,
            pdfView=window.preview.page_mode,pageIds=[p['pageId'] for p in book.state['pages']])
