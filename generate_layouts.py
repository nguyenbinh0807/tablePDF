from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
import collections

from pdfminer.layout import (
    LAParams,
    LTChar,
    LTTextLineHorizontal,
    LTTextLineVertical,
    LTImage
)

def get_pdf_layouts(file_name, char_margin: float = 1.0, line_margin: float = 1.5, 
                word_margin: float = 0.1, detect_vertical: bool = True, all_texts: bool = True):
    """
    TODO: Extract the layout of a PDF file
    ?Param file_name: Path to the PDF file
    ?Param char_margin: Margin between characters
    ?Param line_margin: Margin between lines
    ?Param word_margin: Margin between words
    ?Param detect_vertical: Detect vertical text
    ?Param all_texts: Extract all texts
    """
    with open(file_name, "rb") as file:
        parser = PDFParser(file)
        document = PDFDocument(parser)
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        # Create a PDF resource manager object that stores shared resources
        laparams = LAParams(
            char_margin = char_margin,
            line_margin = line_margin,
            word_margin = word_margin,
            detect_vertical = detect_vertical,
            all_texts = all_texts
        )
        rsrcmgr = PDFResourceManager() # Create a PDF resource manager object that stores shared resources
        device = PDFPageAggregator(rsrcmgr, laparams = laparams) # Create a PDF device object
        interpreter = PDFPageInterpreter(rsrcmgr, device) # Create a PDF interpreter object
        layouts = collections.defaultdict(dict)
        page_number = 1
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()
            layouts[f"page_{page_number}"]["layout"] = layout
            layouts[f"page_{page_number}"]["dim"] = (layout.bbox[2], layout.bbox[3])
            page_number += 1
        return layouts

def get_text_objects(layout, ltype="char", t=None):
    """
    TODO: Recursively parses pdf layout to get a list of PDFMiner text objects.
    ?Param layout: PDFMiner layout object
    ?Param ltype: Type of text object to extract
    """
    if ltype == "char":
        LTObject = LTChar
    elif ltype == "image":
        LTObject = LTImage
    elif ltype == "horizontal_text":
        LTObject = LTTextLineHorizontal
    elif ltype == "vertical_text":
        LTObject = LTTextLineVertical
    if t is None:
        t = []
    try:
        for obj in layout._objs:
            if isinstance(obj, LTObject):
                t.append(obj)
            else:
                t += get_text_objects(obj, ltype=ltype)
    except AttributeError as e:
        pass
    return t