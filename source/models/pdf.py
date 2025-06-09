import re
from PyPDF2 import PdfReader
from date_regex import DateRegexExtractor
import logging
import time
from path import Path


class PdfExtractor(DateRegexExtractor):
    """
    A class to handle PDF reading and extraction of dates using regex patterns.
    """

    def extract_text_from_pdf(self, pdf_path, max_pages=9999999):
        """
        Read text from a PDF file, up to a maximum number of pages. 

        :param pdf_path: Path to the PDF file.
        :return: List of strings, one per page, containing the text from each page.
        """
        texts = []
        with open(pdf_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            number_of_pages = len(reader.pages)
            
            for i in range(min(max_pages, number_of_pages)):
                page = reader.pages[i]
                text = page.extract_text()
                if text:
                    texts.append(text)
        return texts


    def extract_date_pattern(self, texts):
        """
        Iterate over the text pages, and return the first sentence that matches a date pattern.
        
        :param texts: List of strings, one per page, containing the text from each page.
        :return: The sentence that matches the date pattern, or None if no date is found.
        """
        for text in texts:
            sentences = text.split('\n')
            pattern_id = self.find_date_pattern(sentences)
            if pattern_id is not None:
                return sentences[pattern_id].strip()
        return None

    def extract(self, pdf_path, max_pages=9999999):
        """
        Main process to extract the date.

        :param pattern: The date pattern to extract.
        :return: The date normalized to 'dd/mm/yyyy' format, or None if no date is found.
        """
        texts = self.extract_text_from_pdf(pdf_path)
        if not texts:
            return None
        date_pattern = self.extract_date_pattern(texts)
        if not date_pattern:
            return None
        date = self.extract_and_format_date(date_pattern)
        if not date:
            return None        
        return date
    
if __name__ == "__main__":
    extract = PdfExtractor()
    file_path = r"test-data\Large-Data\HDPhuLucphatsinhBACHTRUNGTHANH.pdf"
    start_time = time.time()
    result = extract.extract(file_path)
    end_time = time.time()
    logging.info(f"Date: {result} - {Path(file_path).name} - {end_time - start_time:.2f} seconds\n")
    
    