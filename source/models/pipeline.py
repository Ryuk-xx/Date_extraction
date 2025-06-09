from path import Path
from image_pdf import OcrExtractor
from pdf import PdfExtractor
from doc import DocxExtractor
import PyPDF2
# import subprocess
import os
import time
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.logging_config import setup_logging

# Initialize the logger
logger = setup_logging()

class PipelineExtractor:
    def __init__(self, max_pdf_pages=10):
        self.ocr_extractor = OcrExtractor(max_pdf_pages)
        self.pdf_extractor = PdfExtractor()
        self.docx_extractor = DocxExtractor()
        self.logger = logger

    def check_file_type(self, file_path):
        """
        Check the file type (PDF, DOCX, or DOC).
        """
        if file_path.lower().endswith(".pdf"):
            return "pdf"
        elif file_path.lower().endswith(".docx"):
            return "docx"
        elif file_path.lower().endswith(".doc"):
            return "doc"
        return None

    def check_vietnamese_chars(self, text):
        """
        Check if the text contains Vietnamese characters by matching Vietnamese-specific ASCII characters.

        :param text: Text content to search.
        :return: True if Vietnamese characters are found, False otherwise.
        """
        vietnamese_pattern = r'[\u00C0-\u00FF\u0102\u0103\u0110\u0111\u1EA0-\u1EFF]'
        return bool(re.search(vietnamese_pattern, text))


    def check_pdf_type(self, file_path):
        """
        Check if a PDF file contains text or is a scanned image.

        :param file_path: Path to the PDF file.
        :return: 
            - 0 if the text-based PDF 
            - 1 if the scanned image or handwriting PDF.
        """
        try:
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)

                if len(reader.pages) > 0:
                    first_page = reader.pages[0]
                    last_page = reader.pages[-1]
                    text = first_page.extract_text() + last_page.extract_text()
                    if text.strip() and self.check_vietnamese_chars(text):
                        return 0
            return 1 
        except Exception as e:
            self.logger.info(f"Error reading PDF file: {e}")
            return 1
            
    def convert_doc_to_docx(self, input_file):
        return "hehe.doc" 
    #     """
    #     Converts .doc to .docx using unoconv (for macOS/Linux).
    #     Returns the path to the converted .docx file.
    #     """
    #     output_file = input_file.replace(".doc", ".docx")
        
    #     # Gọi lệnh chuyển đổi
    #     result = subprocess.run(
    #         ['libreoffice', '--headless', '--convert-to', 'docx', input_file, '--outdir', os.path.dirname(input_file)],
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE
    #     )

    #     # Kiểm tra xem file có được tạo không
    #     if os.path.exists(output_file):
    #         print(f"Converted: {output_file}")
    #         return output_file
    #     else:
    #         print("Error in conversion:", result.stderr.decode())
    #         raise FileNotFoundError(f"Conversion failed: {input_file} to {output_file}")

    def extract_date(self, file_path):
        """
        Extract the date from the file metadata.
        
        :param file_path: Path to the file. (docx or pdf)
        :return: Date string in 'DD-MM-YYYY' format or None if not found.
        """
        try:
            start_time = time.time()
            date = None
            file_type = self.check_file_type(file_path)
            if file_type == "doc":
                pass
            elif file_type == "docx":
                date = self.docx_extractor.extract(file_path)
            elif file_type == "pdf":
                # if pdf is text-based, extract date, if error, extract scanned image (backup)
                if self.check_pdf_type(file_path) == 0:
                    date = self.pdf_extractor.extract(file_path)
                    if date is None:
                        date = self.ocr_extractor.extract(file_path)
                else:
                    date = self.ocr_extractor.extract(file_path)
            elif os.path.isdir(file_path):
                pass
            else:
                self.logger.error(f"Unsupported file type: Only PDF and DOCX are allowed")
                raise ValueError("Unsupported file type. Only PDF and DOCX are allowed.")
                
            end_time = time.time()
            self.logger.info(f"Date: {date} - File: {Path(file_path).name} - Time: {end_time - start_time:.2f} seconds")
            return date
        
        except Exception as e:
            self.logger.error(f"Failed to extract {file_path}: {e}\n")
            return None


if __name__ == "__main__":
    folder_path = r"test-data"
    pipeline = PipelineExtractor(max_pdf_pages=11)
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        date = pipeline.extract_date(file_path)