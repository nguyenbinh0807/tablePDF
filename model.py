from generate_file import download_pdf, delete_all_files_in_folder
from generate_layouts import get_pdf_layouts, get_text_objects
from generate_images import convert_pdf_to_img, adaptive_threshold, scale_image
from generate_text import segments_in_bbox, text_in_bbox
from generate_table import Table
from generate_index_table import get_table_index, reduce_index
from utils import find_lines, find_contours, find_joints, merge_close_lines
from itertools import zip_longest


class PDF_TABLE:
    def __init__(self, url, folder, page_pdf_list):
        self.url = url
        self.folder = folder
        self.page_pdf_list = page_pdf_list
        self.table_pdf_dict = {}
    
    
    def _generate_images(self, path_img, dim):
        """
        TODO: Generate images for table extraction
        ?param path_img: Path to the image
        ?param dim: Dimensions of the PDF
        """
        img, threshold = adaptive_threshold(image_file = path_img)
        pdf_width, pdf_height = dim
        image_width, image_height = img.shape[1], img.shape[0]
        
        image_width_scaler = image_width / float(pdf_width)
        image_height_scaler = image_height / float(pdf_height)
        pdf_width_scaler = pdf_width / float(image_width)
        pdf_height_scaler = pdf_height / float(image_height)
        
        image_scalers = (image_width_scaler, image_height_scaler, pdf_height)
        pdf_scalers = (pdf_width_scaler, pdf_height_scaler, image_height)
        return threshold, image_scalers, pdf_scalers
    
    def _generate_rows_and_columns(self, tk, table_bbox):
        cols, rows = zip(*table_bbox[tk])
        cols, rows = list(cols), list(rows)
        cols.extend([tk[0], tk[2]])
        rows.extend([tk[1], tk[3]])
        
        cols = merge_close_lines(sorted(cols), line_tol=2)
        rows = merge_close_lines(sorted(rows, reverse=True), line_tol=2)
        cols = [(cols[index], cols[index + 1]) for index in range(0, len(cols) - 1)]
        rows = [(rows[index], rows[index + 1]) for index in range(0, len(rows) - 1)]
        return rows, cols
    
    def _generate_data(self, rows, cols, vertical_segments, horizontal_segments, t_bbox):
        table = Table(cols, rows)
        #? set  the segments in table
        table = table.set_edges(vertical_segments, horizontal_segments, joint_tol=2)
        #? set border of the table edges to True
        table = table.set_border()
        #? set spanning cells to True
        table = table.set_span()
        pos_errors = []
        direction = "horizontal"
        for text in t_bbox[direction]:
            indices, error = get_table_index(
                table = table,
                t = text,
                direction = direction,
            )
            if indices[:2] != (-1, -1):
                pos_errors.append(error)
                indices = reduce_index(
                    table, indices,
                    ["b", "t"]
                )
                for row_index, column_index, text in indices:
                    table.cells[row_index][column_index].text = text
        return table.data
    
    def _generate_table(self, horizontal_dmask, horizontal_lines, vertical_dmask, vertical_lines, horizontal_text, pdf_scalers):
        """
        TODO: Generate table from the images
        ?param horizontal_dmask: Horizontal mask
        ?param horizontal_lines: Horizontal lines
        ?param vertical_dmask: Vertical mask
        ?param vertical_lines: Vertical lines
        ?param horizontal_text: Horizontal text
        ?param pdf_scalers: PDF scalers
        """
        contours = find_contours(vertical_dmask, horizontal_dmask)
        
        table_bbox = find_joints(
            contours = contours,
            vertical = vertical_dmask,
            horizontal = horizontal_dmask
        )
        table_bbox, vertical_lines, horizontal_lines = scale_image(
            tables = table_bbox,
            v_segments=vertical_lines,
            h_segments=horizontal_lines,
            factors=pdf_scalers
        )
        data_list = []
        t_bbox = {}
        for table_index, tk in enumerate(
            sorted(table_bbox.keys(), key = lambda x: x[1], reverse = True)
        ):
            vertical_segments, horizontal_segments = segments_in_bbox(
                bbox = tk,
                v_segments = vertical_lines,
                h_segments = horizontal_lines
            )
            t_bbox["horizontal"] = text_in_bbox(tk, horizontal_text)
            t_bbox["horizontal"].sort(key = lambda x: (-x.y0, x.x0))
            
            rows, cols = self._generate_rows_and_columns(
                tk = tk,
                table_bbox = table_bbox
            )
            
            data = self._generate_data(
                rows = rows,
                cols = cols,
                vertical_segments = vertical_segments,
                horizontal_segments = horizontal_segments,
                t_bbox = t_bbox
            )
            data_list.extend(data)
        return data_list
    
    def extract_table(self, layouts, page_pdf, path_img):
        layout = layouts[f"page_{page_pdf}"]["layout"] # lấy layout của pdf
        dim = layouts[f"page_{page_pdf}"]["dim"] # lấy kích thước của pdf
        horizontal_text = get_text_objects(layout, ltype="horizontal_text") # lấy text theo chiều ngang
        
        threshold, image_scalers, pdf_scalers = self._generate_images(path_img, dim)
        
        horizontal_dmask, horizontal_lines = find_lines(
            threshold=threshold,
            direction="horizontal",
            line_scale=15,
            iterations=0
        )
        
        vertical_dmask, vertical_lines = find_lines(
            threshold=threshold,
            direction="vertical",
            line_scale=15,
            iterations=0
        )
        
        data = self._generate_table(
            horizontal_dmask = horizontal_dmask,
            horizontal_lines = horizontal_lines,
            vertical_dmask = vertical_dmask,
            vertical_lines = vertical_lines,
            horizontal_text = horizontal_text,
            pdf_scalers = pdf_scalers
        )
        return data
    
    def run(self):
        # Download PDF file
        file_name = download_pdf(
            url = self.url,
            folder = self.folder
        )
        # settings for LLPRAMS
        layout_kwargs = {
        'char_margin': 1.0, 
        'line_margin': 0.5, 
        'word_margin': 0.1, 
        'detect_vertical': True, 
        'all_texts': True
        }
        # Extract layouts
        layouts = get_pdf_layouts(file_name = file_name, **layout_kwargs)
        path_img_list = convert_pdf_to_img(file_name = file_name, folder=self.folder, pages = self.page_pdf_list)
        
        for page_pdf, path_img in zip_longest(self.page_pdf_list, path_img_list):
            data = self.extract_table(
                layouts = layouts,
                page_pdf = page_pdf,
                path_img = path_img
            )
            self.table_pdf_dict[f"page_{page_pdf}"] = data
        print("Table extraction completed successfully.")
        delete_all_files_in_folder(folder_path = self.folder)
        print("All images have been deleted successfully.")