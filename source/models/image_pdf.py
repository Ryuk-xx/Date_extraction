import os
import time
import logging
from ocr import Ocr
from path import Path
from pdf2image import convert_from_path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.logging_config import setup_logging

# Initialize the logger
logger = setup_logging("ScanPdfExtractor")

ocr = Ocr(
    logger = logger,
    save_crop_img=True,
    save_folder="temp_save/",
)
        
class OcrExtractor():
    def __init__(self, max_pages=10):
        self.max_pages = max_pages
        self.logger = logger
        
    def process_single_page_pdf(self, file_path, page_num, page_image=None):
        """
        Process a single page asynchronously based on its type.
        """
        page_start = time.time()
        try:
            date = ocr.process_page(
                pdf_path=file_path,
                page_num=page_num + 1,
                page_image=page_image,
            )

            # measure total runtime for this page
            page_end = time.time()
            page_run_time = page_end - page_start
            
            if date:
                if date == "Blank date": # find pattern having regex but date is blank
                    self.logger.info(f"Page {page_num + 1} - Blank Date - {page_run_time:.2f} seconds.")
                else:
                    self.logger.info(f"Page {page_num + 1} - Found Date: {date} - {page_run_time:.2f} seconds.")
                return date
            else:
                self.logger.info(f"Page {page_num + 1} - No Date - {page_run_time:.2f} seconds.")
                return None
        
            
        except Exception as e:
            self.logger.error(f"Page {page_num + 1} - Error processing: {e}")
            return None

        

    def extract(self, file_path):
        """
        Process pages sequentially based on document type.

        :param file_path: Path to the document file.
        :return: Extracted date or None.
        """
        def pdf_pages_to_image(pdf_path, n_pages=500):
            """
            return a list of page images from a PDF.
            """
            list_images = convert_from_path(pdf_path,
                                            first_page=1, 
                                            last_page=n_pages, 
                                            dpi=300)
            return list_images, len(list_images)
        try:
            list_images, num_pages = pdf_pages_to_image(file_path, self.max_pages)
            max_pages = min(self.max_pages, num_pages)
            if num_pages == 0:
                self.logger.warning("No pages found in the document.")
                return None

            for page_num in range(max_pages):
                date = self.process_single_page_pdf(file_path, page_num, list_images[page_num])
                if date:
                    if date == "Blank date": 
                        return None
                    else:                     
                        return date
            return None
        except Exception as e:
            self.logger.error(f"Error reading file: {e}")
            return None

if __name__ == "__main__":
    file_path = r"D:/contract_date_extractor/temp/2025-05-27/1748343684392.pdf"
    start_time = time.time()
    extractor = OcrExtractor(max_pages=11)
    result = extractor.extract(file_path)
    end_time = time.time()
    logger.info(f"Date: {result} - {Path(file_path).name} - {end_time - start_time:.2f} seconds\n")

