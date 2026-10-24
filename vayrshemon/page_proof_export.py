"""Export the visible PNG or SVG pages together from one frozen revision."""
from pathlib import Path
from PySide6.QtWidgets import QFileDialog,QMessageBox
from tools.m0.common import file_hash
from .page_view import arrangement
from .pages import page_rect
from .proof_options import supported_dpi
from .proof_names import suggested_proof_path,spread_proof_paths


def export_pages(window,kind):
    if kind not in ('png','svg'):raise ValueError('SPREAD_PROOF_FORMAT')
    label=kind.upper();suffix='.'+kind
    book=window.book;spread=window.preview.page_mode=='two'
    pages=[p for p,_ in arrangement(book,window.preview.page_mode)]
    requested=int(window.proof_dpi.value())
    try:dpi=min(supported_dpi(page_rect(p),requested) for p in pages)
    except ValueError as error:window.statusBar().showMessage(str(error),30000);return
    suggestion=suggested_proof_path(book,kind)
    if spread:suggestion=spread_proof_paths(suggestion,len(pages),kind)[0]
    title=f'Export {len(pages)} {label} pages · {dpi} DPI' if spread else f'Export {label} · {dpi} DPI'
    path,_=QFileDialog.getSaveFileName(window,title,suggestion,f'{label} (*{suffix})',options=QFileDialog.Option.DontConfirmOverwrite)
    if not path:return
    paths=spread_proof_paths(path,len(pages),kind) if spread else [path if path.lower().endswith(suffix) else path+suffix]
    hashes=[];existing=[]
    for name in paths:
        target=Path(name)
        if target.exists() and not target.is_file():window.statusBar().showMessage('Export path must be a file: '+name,30000);return
        hashes.append(file_hash(target) if target.exists() else None)
        if target.exists():existing.append(name)
    if existing and QMessageBox.question(window,f'Replace {label} proofs?','Replace these files when rendering finishes?\n\n'+'\n'.join(existing),QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
    params=dict(path=path if spread else paths[0],format=kind,mode=book.view['mode'],dpi=dpi,raster_policy='raster')
    if spread:params.update(page_ids=[p['pageId'] for p in pages],replace_sha256s=hashes)
    else:
        params['page_id']=pages[0]['pageId']
        if hashes[0] is not None:params['replace_sha256']=hashes[0]
    result=window.invoke('jobs.export',**params)
    if result:
        window.poll_jobs();window.statusBar().showMessage(f'Exporting {len(paths)} {label} file(s) at {dpi} DPI · '+' · '.join(paths),30000)
        book.log.emit('publication','DESKTOP_PROOF_REQUESTED',requestedDpi=requested,actualDpi=dpi,paths=paths,pageIds=[p['pageId'] for p in pages])
