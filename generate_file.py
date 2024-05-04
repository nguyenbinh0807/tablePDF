import os
import requests

def download_pdf(url: str = None, folder: str = None):
    """
    TODO: Download a PDF file from a given URL and save it to a folder
    ? param url: URL of the PDF file
    ? param folder: Folder to save the PDF file
    """
    if not os.path.exists(folder):
        print(f"not folder is {folder}")
    response = requests.get(url)
    if response.status_code == 200:
        file_name = url.split("/")[-1]
        file_path = os.path.join(folder, file_name)
        with open(file_path, "wb") as file:
            file.write(response.content)
            return file_path
    else:
        return None

def delete_all_files_in_folder(folder_path: str = None):
    """
    TODO: Delete all files in a folder
    ? param folder_path: Path to the folder
    """
    # Kiểm tra xem thư mục có tồn tại không
    if not os.path.exists(folder_path):
        print(f"The directory {folder_path} does not exist.")
        return

    # Liệt kê tất cả các file trong thư mục
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)  # Xóa file
                print(f"File {file_path} has been deleted successfully.")
            elif os.path.isdir(file_path):
                print(f"Skipping directory: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

