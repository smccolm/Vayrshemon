"""PDF viewing metadata; page content, fonts and dimensions are retained."""
from io import BytesIO
from pypdf import PdfReader,PdfWriter,Transformation
from pypdf.generic import FloatObject,RectangleObject


class _PagePoint(FloatObject):
    # Native dimensions have six decimal point places; pypdf's default
    # significant-digit formatting rounds the last places on larger pages.
    def myrepr(self):return f'{self:.6f}'.rstrip('0').rstrip('.') or '0'


def with_view(path,mode,page_sizes):
    if mode not in ('one','two'):raise ValueError('UNKNOWN_PDF_VIEW_MODE')
    with open(path,'rb') as stream:
        writer=PdfWriter(clone_from=PdfReader(stream))
        if not writer.pages:raise ValueError('EMPTY_PDF')
        if len(writer.pages)!=len(page_sizes):raise ValueError('PDF_PAGE_COUNT_MISMATCH')
        # Qt writes integer-point page boxes. Render into enclosing boxes, then
        # restore the exact physical sizes while keeping every top-left origin.
        for page,(width,height) in zip(writer.pages,page_sizes):
            offset=height-float(page.mediabox.height)
            if offset:page.add_transformation(Transformation().translate(0,offset))
            bounds=[_PagePoint(v) for v in (0,0,width,height)]
            page.mediabox=RectangleObject(bounds)
            page.cropbox=RectangleObject(bounds)
        writer.pdf_header=max(writer.pdf_header,'%PDF-1.5')
        writer.page_layout='/SinglePage' if mode=='one' else '/TwoPageLeft'
        writer.page_mode='/UseNone'
        writer.create_viewer_preferences().direction='/L2R'
        writer.set_page_label(0,len(writer.pages)-1,style='/D',start=1)
        writer.open_destination=writer.pages[0]
        output=BytesIO();writer.write(output)
        return output.getvalue()
