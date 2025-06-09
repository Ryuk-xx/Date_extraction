import re
from docx import Document
import logging
from date_regex import DateRegexExtractor
import time
from path import Path


class DocxExtractor(DateRegexExtractor):
    """
    A class to handle DOCX reading and extraction of date
    """

    def extract_text_from_docx(self, docx_path):
        """
        Reads the content of a DOCX file (since DOCX is not paginated like PDFs, it returns the full text).

        :param page_num: Unused, included for interface consistency.
        :return: The content of the document as a string.
        """
        try:
            doc = Document(docx_path)
            content = "\n".join([para.text for para in doc.paragraphs])
            return content
        except Exception as e:
            return None


    def extract_date_pattern(self, content):
        """
        Return the first sentence that matches a date pattern.
        
        :param texts: all content in 1 document.
        :return: The sentence that matches the date pattern, or None if no date is found.
        """
        
        sentences = content.split('\n')
        pattern_id = self.find_date_pattern(sentences)
        if pattern_id is not None:
            return sentences[pattern_id].strip()
        return None

    def extract(self, docx_path):
        """
        Main process to extract the date.

        :param pattern: The date pattern to extract.
        :return: The date normalized to 'dd/mm/yyyy' format, or None if no date is found.
        """
        content = self.extract_text_from_docx(docx_path)
        if not content:
            return None
        
        date_pattern = self.extract_date_pattern(content)
        if not date_pattern:
            return None
        
        date = self.extract_and_format_date(date_pattern)
        if not date:
            return None      
        else:
            return date
    
if __name__ == "__main__":
    extract = DocxExtractor()
    file_path = r"D:\contract_date_extractor\test-data\HD 180201 BGG- SPMIENBAC.docx"
    start_time = time.time()
    result = extract.extract(file_path)
    end_time = time.time()
    logging.info(f"Date: {result} - {Path(file_path).name} - {end_time - start_time:.2f} seconds\n")
    
    