"""Refresh the native dictionary on demand after a batch of new translations."""
import argparse
import gc
import os
import shutil
from contextlib import contextmanager

from tools.dictionary_corpus import BOOK, EDITION, WORK, read, scan, sha, unpack_witnesses
from tools.dictionary_forms import form_readings
from tools.dictionary_layout import STAGE, premeasure, publish
from tools.dictionary_lexicon import compile_corpus, load_gzip
from tools.dictionary_proof import verify
from tools.dictionary_rows import build_rows


@contextmanager
def edition_lock():
    import msvcrt
    STAGE.mkdir(parents=True,exist_ok=True)
    with (STAGE/'refresh.lock').open('a+b') as lock:
        if lock.tell()==0:
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError as exc:
            raise RuntimeError('Another dictionary refresh is running') from exc
        try:
            yield
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)


def refresh(resume,workers):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    with edition_lock():
        if resume=='verify':
            verify()
            return
        target=BOOK/(EDITION+'.vay')
        generated=['publication.json','verification.json','page-index.json','attestations.json.gz',
                   'manuscript-readings.json.gz','dictionary-rows.json.gz']
        backup=None
        if target.exists():
            receipt=WORK/'publication.json'
            old_hash=sha(target)
            if not receipt.is_file() or read(receipt)['sha256']!=old_hash:
                raise ValueError('The published native dictionary has independent edits. Reconcile those edits before refreshing.')
            backup=STAGE/'editions'/old_hash
            backup.mkdir(parents=True,exist_ok=True)
            for path in [target,*(WORK/name for name in generated),*(WORK.glob('*.txt'))]:
                if path.is_file() and not (backup/path.name).exists():
                    shutil.copy2(path,backup/path.name)
        try:
            if resume=='corpus':
                unpack_witnesses()
                scan()
                compile_corpus()
                form_readings()
                from tools.dictionary_sentence_witnesses import build as collect_sentence_witnesses
                collect_sentence_witnesses()
                from tools.dictionary_example_evidence import build as collect_contexts
                collect_contexts()
            if load_gzip(WORK/'attestations.json.gz')['unresolvedKeys']:
                raise ValueError('New semantic keys need definitions before issuing the dictionary.')
            build_rows()
            rows=load_gzip(WORK/'dictionary-rows.json.gz')['rows']
            premeasure(rows,workers)
            del rows
            publish()
            gc.collect()
            verify()
        except BaseException:
            if backup:
                for path in [target,*(WORK/name for name in generated)]:
                    prior=backup/path.name
                    if prior.exists():
                        tmp=path.with_suffix(path.suffix+'.restoring')
                        shutil.copy2(prior,tmp)
                        tmp.replace(path)
            raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from',dest='resume',choices=['corpus','entries','verify'],default='corpus',
                        help='Reinventory sources, recompile existing attestations, or verify the publication.')
    parser.add_argument('--workers',type=int,default=8,help='Number of typesetting processes')
    args=parser.parse_args()
    if args.workers<1:parser.error('--workers must be a positive integer')
    refresh(args.resume,args.workers)
