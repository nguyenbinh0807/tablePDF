from pdfminer.layout import LTChar, LTAnno
from operator import itemgetter
from itertools import groupby
import numpy as np
import re

def segments_in_bbox(bbox, v_segments, h_segments):
    lb = (bbox[0], bbox[1])
    rt = (bbox[2], bbox[3])
    v_s = [
        v
        for v in v_segments
        if v[1] > lb[1] - 2 and v[3] < rt[1] + 2 and lb[0] - 2 <= v[0] <= rt[0] + 2
    ]
    h_s = [
        h
        for h in h_segments
        if h[0] > lb[0] - 2 and h[2] < rt[0] + 2 and lb[1] - 2 <= h[1] <= rt[1] + 2
    ]
    return v_s, h_s

def text_in_bbox(bbox, text):
    """
    TODO: Returns all text objects present inside a bounding box.

    ?Parameters
    ----------
    ?bbox : tuple
        Tuple (x1, y1, x2, y2) representing a bounding box where
        (x1, y1) -> lb and (x2, y2) -> rt in the PDF coordinate
        space.
    ?text : List of PDFMiner text objects.

    !Returns
    -------
    ?t_bbox : list
        List of PDFMiner text objects that lie inside table.

    """
    lb = (bbox[0], bbox[1])
    rt = (bbox[2], bbox[3])
    t_bbox = [
        t
        for t in text
        if lb[0] - 2 <= (t.x0 + t.x1) / 2.0 <= rt[0] + 2
        and lb[1] - 2 <= (t.y0 + t.y1) / 2.0 <= rt[1] + 2
    ]
    return t_bbox


def text_strip(text, strip=""):
    """Strips any characters in `strip` that are present in `text`.
    Parameters
    ----------
    text : str
        Text to process and strip.
    strip : str, optional (default: '')
        Characters that should be stripped from `text`.
    Returns
    -------
    stripped : str
    """
    if not strip:
        return text

    stripped = re.sub(
        r"[{}]".format("".join(map(re.escape, strip))), "", text, re.UNICODE
    )
    return stripped

def flag_font_size(textline, direction, strip_text=""):
    """Flags super/subscripts in text by enclosing them with <s></s>.
    May give false positives.

    Parameters
    ----------
    textline : list
        List of PDFMiner LTChar objects.
    direction : string
        Direction of the PDFMiner LTTextLine object.
    strip_text : str, optional (default: '')
        Characters that should be stripped from a string before
        assigning it to a cell.

    Returns
    -------
    fstring : string

    """
    if direction == "horizontal":
        d = [
            (t.get_text(), np.round(t.height, decimals=6))
            for t in textline
            if not isinstance(t, LTAnno)
        ]
    elif direction == "vertical":
        d = [
            (t.get_text(), np.round(t.width, decimals=6))
            for t in textline
            if not isinstance(t, LTAnno)
        ]
    l = [np.round(size, decimals=6) for text, size in d]
    if len(set(l)) > 1:
        flist = []
        min_size = min(l)
        for key, chars in groupby(d, itemgetter(1)):
            if key == min_size:
                fchars = [t[0] for t in chars]
                if "".join(fchars).strip():
                    fchars.insert(0, "<s>")
                    fchars.append("</s>")
                    flist.append("".join(fchars))
            else:
                fchars = [t[0] for t in chars]
                if "".join(fchars).strip():
                    flist.append("".join(fchars))
        fstring = "".join(flist)
    else:
        fstring = "".join([t.get_text() for t in textline])
    return text_strip(fstring, strip_text)


def split_textline(table, textline, direction, flag_size=False, strip_text=""):
    """Splits PDFMiner LTTextLine into substrings if it spans across
    multiple rows/columns.

    Parameters
    ----------
    table : camelot.core.Table
    textline : object
        PDFMiner LTTextLine object.
    direction : string
        Direction of the PDFMiner LTTextLine object.
    flag_size : bool, optional (default: False)
        Whether or not to highlight a substring using <s></s>
        if its size is different from rest of the string. (Useful for
        super and subscripts.)
    strip_text : str, optional (default: '')
        Characters that should be stripped from a string before
        assigning it to a cell.

    Returns
    -------
    grouped_chars : list
        List of tuples of the form (idx, text) where idx is the index
        of row/column and text is the an lttextline substring.

    """
    idx = 0
    cut_text = []
    bbox = textline.bbox
    try:
        if direction == "horizontal" and not textline.is_empty():
            x_overlap = [
                i
                for i, x in enumerate(table.cols)
                if x[0] <= bbox[2] and bbox[0] <= x[1]
            ]
            r_idx = [
                j
                for j, r in enumerate(table.rows)
                if r[1] <= (bbox[1] + bbox[3]) / 2 <= r[0]
            ]
            r = r_idx[0]
            x_cuts = [
                (c, table.cells[r][c].x2) for c in x_overlap if table.cells[r][c].right
            ]
            if not x_cuts:
                x_cuts = [(x_overlap[0], table.cells[r][-1].x2)]
            for obj in textline._objs:
                row = table.rows[r]
                for cut in x_cuts:
                    if isinstance(obj, LTChar):
                        if (
                            row[1] <= (obj.y0 + obj.y1) / 2 <= row[0]
                            and (obj.x0 + obj.x1) / 2 <= cut[1]
                        ):
                            cut_text.append((r, cut[0], obj))
                            break
                        else:
                            # TODO: add test
                            if cut == x_cuts[-1]:
                                cut_text.append((r, cut[0] + 1, obj))
                    elif isinstance(obj, LTAnno):
                        cut_text.append((r, cut[0], obj))
        elif direction == "vertical" and not textline.is_empty():
            y_overlap = [
                j
                for j, y in enumerate(table.rows)
                if y[1] <= bbox[3] and bbox[1] <= y[0]
            ]
            c_idx = [
                i
                for i, c in enumerate(table.cols)
                if c[0] <= (bbox[0] + bbox[2]) / 2 <= c[1]
            ]
            c = c_idx[0]
            y_cuts = [
                (r, table.cells[r][c].y1) for r in y_overlap if table.cells[r][c].bottom
            ]
            if not y_cuts:
                y_cuts = [(y_overlap[0], table.cells[-1][c].y1)]
            for obj in textline._objs:
                col = table.cols[c]
                for cut in y_cuts:
                    if isinstance(obj, LTChar):
                        if (
                            col[0] <= (obj.x0 + obj.x1) / 2 <= col[1]
                            and (obj.y0 + obj.y1) / 2 >= cut[1]
                        ):
                            cut_text.append((cut[0], c, obj))
                            break
                        else:
                            # TODO: add test
                            if cut == y_cuts[-1]:
                                cut_text.append((cut[0] - 1, c, obj))
                    elif isinstance(obj, LTAnno):
                        cut_text.append((cut[0], c, obj))
    except IndexError:
        return [(-1, -1, textline.get_text())]
    grouped_chars = []
    for key, chars in groupby(cut_text, itemgetter(0, 1)):
        if flag_size:
            grouped_chars.append(
                (
                    key[0],
                    key[1],
                    flag_font_size(
                        [t[2] for t in chars], direction, strip_text=strip_text
                    ),
                )
            )
        else:
            gchars = [t[2].get_text() for t in chars]
            grouped_chars.append(
                (key[0], key[1], text_strip("".join(gchars), strip_text))
            )
    return grouped_chars