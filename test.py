from model import PDF_TABLE
url = "https://ssiam.com.vn/upload/files/QuanLyQuy/SSISCA_FMS%20FORM_KY%20SO_Thang_012024.pdf"
page_pdf_number = [1, 2, 3, 9]
folder = "pdf_data"
pdf_table = PDF_TABLE(
    url=url,
    folder=folder,
    page_pdf_list=page_pdf_number
)
pdf_table.run()
print(pdf_table.table_pdf_dict)