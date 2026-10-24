"""Compatibility entry point for the PNG button and older milestone windows."""
from PySide6.QtWidgets import QFileDialog,QMessageBox
from .page_proof_export import export_pages


def export_png(window):
    return export_pages(window,'png')
