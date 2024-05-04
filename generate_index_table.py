import re
import warnings
from generate_text import flag_font_size, split_textline

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
    
def get_table_index(
    table, t, direction, split_text=False, flag_size=False, strip_text=""
):
    r_idx, c_idx = [-1] * 2
    for r in range(len(table.rows)):
        if (t.y0 + t.y1) / 2.0 < table.rows[r][0] and (t.y0 + t.y1) / 2.0 > table.rows[
            r
        ][1]:
            lt_col_overlap = []
            for c in table.cols:
                if c[0] <= t.x1 and c[1] >= t.x0:
                    left = t.x0 if c[0] <= t.x0 else c[0]
                    right = t.x1 if c[1] >= t.x1 else c[1]
                    lt_col_overlap.append(abs(left - right) / abs(c[0] - c[1]))
                else:
                    lt_col_overlap.append(-1)
            if len(list(filter(lambda x: x != -1, lt_col_overlap))) == 0:
                text = t.get_text().strip("\n")
                text_range = (t.x0, t.x1)
                col_range = (table.cols[0][0], table.cols[-1][1])
                warnings.warn(
                    "{} {} does not lie in column range {}".format(
                        text, text_range, col_range
                    )
                )
            r_idx = r
            c_idx = lt_col_overlap.index(max(lt_col_overlap))
            break

    # error calculation
    y0_offset, y1_offset, x0_offset, x1_offset = [0] * 4
    if t.y0 > table.rows[r_idx][0]:
        y0_offset = abs(t.y0 - table.rows[r_idx][0])
    if t.y1 < table.rows[r_idx][1]:
        y1_offset = abs(t.y1 - table.rows[r_idx][1])
    if t.x0 < table.cols[c_idx][0]:
        x0_offset = abs(t.x0 - table.cols[c_idx][0])
    if t.x1 > table.cols[c_idx][1]:
        x1_offset = abs(t.x1 - table.cols[c_idx][1])
    X = 1.0 if abs(t.x0 - t.x1) == 0.0 else abs(t.x0 - t.x1)
    Y = 1.0 if abs(t.y0 - t.y1) == 0.0 else abs(t.y0 - t.y1)
    charea = X * Y
    error = ((X * (y0_offset + y1_offset)) + (Y * (x0_offset + x1_offset))) / charea

    if split_text:
        return (
            split_textline(
                table, t, direction, flag_size=flag_size, strip_text=strip_text
            ),
            error,
        )
    else:
        if flag_size:
            return (
                [
                    (
                        r_idx,
                        c_idx,
                        flag_font_size(t._objs, direction, strip_text=strip_text),
                    )
                ],
                error,
            )
        else:
            return [(r_idx, c_idx, text_strip(t.get_text(), strip_text))], error


def reduce_index(t, idx, shift_text):
    indices = []
    for r_idx, c_idx, text in idx:
        for d in shift_text:
            if d == "l":
                if t.cells[r_idx][c_idx].hspan:
                    while not t.cells[r_idx][c_idx].left:
                        c_idx -= 1
                        
            if d == "r":
                if t.cells[r_idx][c_idx].hspan:
                    while not t.cells[r_idx][c_idx].right:
                        c_idx += 1
                        
            if d == "t":
                if t.cells[r_idx][c_idx].vspan:
                    while not t.cells[r_idx][c_idx].top:
                        r_idx -= 1
                        
            if d == "b":
                if t.cells[r_idx][c_idx].vspan:
                    while not t.cells[r_idx][c_idx].bottom:
                        r_idx += 1
                        
        indices.append((r_idx, c_idx, text))
    return indices