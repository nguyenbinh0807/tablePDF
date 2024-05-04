from pdf2image import convert_from_path
import os
import cv2
import numpy as np


def convert_pdf_to_img(file_name: str = None, folder: str = None, pages: list = None) -> list:
    output_path_list = []
    
    if pages:
        for page in pages:    
            images = convert_from_path(
                file_name, dpi=300, 
                output_folder = folder, fmt='png',
                poppler_path = r"poppler-24.02.0\Library\bin",
                output_file = os.path.basename(file_name).split(".")[0],
                first_page=page,
                last_page=page
            )
        print([image.filename for image in images])
        output_path_list.extend([image.filename for image in images])
    else:      
        images = convert_from_path(file_name, dpi=300, 
                output_folder = folder, fmt='png',
                poppler_path = r"poppler-24.02.0\Library\bin",
                output_file = os.path.basename(file_name).split(".")[0])
    
        output_path_list.extend([image.filename for image in images])
        
    return output_path_list

def adaptive_threshold(image_file, process_background = False, blocksize = 15, c = -2):
    img = cv2.imread(image_file)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if process_background:
        threshold = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blocksize, c
        )
    else:
        threshold = cv2.adaptiveThreshold(
            np.invert(gray),
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blocksize,
            c,
        )
    return img, threshold


def scale(x, s):
    x *= s
    return x
    
def translate(x1, x2):
    x2 += x1
    return x2

def scale_image(tables, v_segments, h_segments, factors):
    scaling_factor_x, scaling_factor_y, img_y = factors
    tables_new = {}
    for k in tables.keys():
        x1, y1, x2, y2 = k
        x1 = scale(x1, scaling_factor_x)
        y1 = scale(abs(translate(-img_y, y1)), scaling_factor_y)
        x2 = scale(x2, scaling_factor_x)
        y2 = scale(abs(translate(-img_y, y2)), scaling_factor_y)
        j_x, j_y = zip(*tables[k])
        j_x = [scale(j, scaling_factor_x) for j in j_x]
        j_y = [scale(abs(translate(-img_y, j)), scaling_factor_y) for j in j_y]
        joints = zip(j_x, j_y)
        tables_new[(x1, y1, x2, y2)] = joints

    v_segments_new = []
    for v in v_segments:
        x1, x2 = scale(v[0], scaling_factor_x), scale(v[2], scaling_factor_x)
        y1, y2 = (
            scale(abs(translate(-img_y, v[1])), scaling_factor_y),
            scale(abs(translate(-img_y, v[3])), scaling_factor_y),
        )
        v_segments_new.append((x1, y1, x2, y2))

    h_segments_new = []
    for h in h_segments:
        x1, x2 = scale(h[0], scaling_factor_x), scale(h[2], scaling_factor_x)
        y1, y2 = (
            scale(abs(translate(-img_y, h[1])), scaling_factor_y),
            scale(abs(translate(-img_y, h[3])), scaling_factor_y),
        )
        h_segments_new.append((x1, y1, x2, y2))

    return tables_new, v_segments_new, h_segments_new