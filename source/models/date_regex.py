import re
import unicodedata
import datetime

class DateRegexExtractor:
    def normalize_text(sefl, text):
        """
        Normalize text by removing diacritics and punctuation, and converting to lowercase.
        
        :param text: Text to normalize.
        :return: Normalized text.
        """
        nkfd = unicodedata.normalize('NFKD', text)
        text = ''.join(ch for ch in nkfd if unicodedata.category(ch) != 'Mn')
        
        text = re.sub(r'[^a-zA-Z0-9/:]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(?<=\d)\s+(?=\d)', '', text)
        return text.lower()
    
    def is_valid_date(self, day: int, month: int, year: int) -> bool:
        """
        Check if day/month/year (int) form a valid date.
        """
        try:
            datetime.date(int(year), int(month), int(day))
            return True
        except ValueError:
            return False

    def find_date_pattern(self, texts):
        """
        Find date patterns in the recognized text.
        Input:
            texts (list): List of recognized text strings.
        Output:
            date_like_index (int): Index of the text that matches a date pattern, or None if not found.
        """
        # 1. Pattern for "Hôm nay ... ngày ... tháng ... năm ..."
        pattern_homnay = re.compile(
            r'''(?ix)                                # i: ignore-case, x: allow comments
            hom?\s*nay                               # "hom nay" (có thể là "homnay" hoặc "hom nay")
            \s*                                      # optional khoảng trắng sau "hom nay"
            (?:
                # --- Trường hợp 1: ngày dạng dd/mm/yyyy hoặc d/m/yyyy ---
                (?P<slash_date>
                    (?:ngay\s*)?  
                    (\d{1,2})?   # 1–2 chữ số (ngày)
                    \D{0,3} 
                    /\s*
                    (\d{0,2})?       # 1–2 chữ số (tháng)
                    \D{0,3}
                    /\s*
                    (\d{2,4})?      # 2–4 chữ số (năm)
                )
            |
                # --- Trường hợp 2: dạng "ngay <dd> thang <mm> nam <yyyy>" (có thể thiếu số) ---
                (?P<text_date>
                    ngay\s*\D{0,3}\s*(\d{0,2})?       # "ngay" + lỗi + số ngày (tùy chọn)
                    \D{0,3}\s* 
                    thang\s*\D{0,3}\s*(\d{0,2})?      # "thang" + lỗi + số tháng (tùy chọn)
                    \D{0,3}\s* 
                    nam\s*\D{0,3}\s*(\d{0,4})?        # "nam" + lỗi + số năm (tùy chọn)
                )
            |
                # --- Trường hợp 3: chỉ "/ /" sau "hom nay" (không có số) ---
                (?P<empty_slash>
                    /\s*/\s*/?
                )
            )
            ''',
            flags=re.VERBOSE
        )

        # 2. Pattern for "Ngày ký: .. / .. / ...."
        pattern_ngayky = re.compile(
            r'''(?ix)                             # i: ignore-case, x: allow comments
            ngay\s*ky                            # từ "ngay ky" với khoảng trắng tùy ý giữa
            \s*:\s*                              # dấu ":" với khoảng trắng tùy ý xung quanh
            (?:                                  # bắt đầu nhóm không lưu (non-capturing group)
                \d{1,2}/\d{1,2}/\d{4}            # định dạng ngày: dd/mm/yyyy
                |                                # hoặc
                ngay\s*\D{0,3}\s*(\d{0,2})?      # "ngay" + lỗi + số ngày (tùy chọn)
                \D{0,3}\s* 
                thang\s*\D{0,3}\s*(\d{0,2})?     # "thang" + lỗi + số tháng (tùy chọn)
                \D{0,3}\s* 
                nam\s*\D{0,3}\s*(\d{0,4})?       # từ "nam" 
                |                                # hoặc
                ngay\s*thang\s*nam               # từ "ngay thang nam" không có số
                |                                # hoặc
                /?\s*/?\s*/?                     # ba dấu "/" hoặc khoảng trắng (tùy chọn)
            )
            ''',
            flags=re.VERBOSE
        )
        for idx, text in enumerate(texts):
            text = self.normalize_text(text)        
            if pattern_homnay.search(text) or pattern_ngayky.search(text):
                return idx
        return None
    
    
    def extract_and_format_date(self, text):
        """
        Extract a date from a string.

        Args:
            text (str): Text string that may contain a date.

        Returns:
            text (str): The date normalized to 'dd/mm/yyyy' format.
            If no date is found, returns None.
        """
        text = self.normalize_text(text)
    
        # “Slash-like” pattern (dd / mm / yyyy), allows strange characters in between:
        slash_pattern = re.compile(
            r'(\d{1,2})'               # Group 1: day (1 or 2 digits)
            r'\s*'
            r'(?:[\/\s]{1,3})'     # 1–3 separator characters: '/', '.', '-', or space
            r'\s*'
            r'(\d{1,2})'               # Group 2: month (1 or 2 digits)
            r'\s*'
            r'(?:[\/\s]{1,3})'     # Next 1–3 separator characters
            r'\s*'
            r'(\d{4})'                 # Group 3: year (4 digits)
        )

        # “Vietnamese” pattern: dd tháng mm năm yyyy (all lowercased so only 'tháng'/'năm')
        vietnamese_pattern = re.compile(
            r'(\d{1,2})'               # Group 1: day
            r'\s*(?:thang)\s*'   # the word 'tháng'
            r'(\d{1,2})'               # Group 2: month
            r'\s*(?:nam)\s*'   # the word 'năm'
            r'(\d{4})'                 # Group 3: year
        )

        all_patterns = [slash_pattern, vietnamese_pattern]
        for pattern in all_patterns:
            for day_str, month_str, year_str in pattern.findall(text):
                day_fmt   = day_str.zfill(2)
                month_fmt = month_str.zfill(2)
                year_fmt  = year_str
                if self.is_valid_date(day_str, month_str, year_str):
                    return(f"{day_fmt}/{month_fmt}/{year_fmt}")
        return None
    