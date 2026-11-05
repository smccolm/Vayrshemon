"""Visible, bounded loading stages for large native documents."""
from contextlib import contextmanager
from pathlib import Path
from PySide6.QtCore import QEventLoop,Qt
from PySide6.QtWidgets import QApplication,QDialog,QLabel,QProgressBar,QVBoxLayout


@contextmanager
def loading_dialog(book,path):
    window=book.window
    if window is None or book.__dict__.get('loading_reporter'):
        yield
        return
    dialog=QDialog(window)
    dialog.setWindowTitle('Opening document')
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    dialog.setWindowFlag(Qt.WindowType.WindowCloseButtonHint,False)
    layout=QVBoxLayout(dialog)
    layout.addWidget(QLabel(Path(path).name))
    label=QLabel('Reading document…');layout.addWidget(label)
    bar=QProgressBar();bar.setRange(0,100);layout.addWidget(bar)
    dialog.setMinimumWidth(440)
    def report(stage,progress):
        label.setText(stage);bar.setValue(progress)
        # Repaint without dispatching edits while replacing the document.
        dialog.repaint();label.repaint();bar.repaint()
    book.loading_reporter=report
    try:
        dialog.show()
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents |
                                   QEventLoop.ProcessEventsFlag.ExcludeSocketNotifiers)
        yield
    finally:
        book.loading_reporter=None
        dialog.hide();dialog.deleteLater()
