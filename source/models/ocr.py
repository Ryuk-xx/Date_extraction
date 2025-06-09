import matplotlib.pyplot as plt
from PIL import Image
import torch
from pdf2image import convert_from_path
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from paddleocr import PaddleOCR
from date_regex import DateRegexExtractor
import numpy as np
from path import Path 
import cv2
import os 
from datetime import datetime
import logging
logging.getLogger("ppocr").propagate = False
logging.getLogger("ppocr").disabled = True

config = Cfg.load_config_from_name('vgg_seq2seq') 
config['weights'] = r"source\weights\hand_ocr.pth"
config['device'] = 'cuda:0' if torch.cuda.is_available() else 'cpu'
vietocr = Predictor(config)

paddleocr = PaddleOCR(lang='en', cpu_threads=8)


class Ocr(DateRegexExtractor):
    def __init__(self, 
                 logger,
                 save_crop_img=False, 
                 save_folder="temp_save/",):
        
        self.logger = logger
        self.save_crop_img = save_crop_img
        self.save_folder = save_folder

        # Initialize VietOCR with a specific configuration  
        self.vietocr = vietocr       
        self.paddle_ocr = paddleocr
    
    def detect_text(self, image):
        """
        Detect text using PaddleOCR.
        """
        return self.paddle_ocr.ocr(image, cls=True)
    
        
    def save_image(self, img, folder, filename):
        os.makedirs(folder, exist_ok=True)
        
        dated_folder = os.path.join(folder, datetime.now().strftime('%Y-%m-%d'))
        os.makedirs(dated_folder, exist_ok=True)
        
        file_path = os.path.join(dated_folder, filename)
        
        cv2.imwrite(file_path, img)
        self.logger.info(f"Saved image: {file_path}")

    
    def img2text(self, image):
        result = self.vietocr.predict(image)
        return result      


    def process_page(self, pdf_path, page_num=1, page_image=None):
        """
        Process a PDF page to extract the contract date using OCR and handwriting recognition.
        """
        file_name = Path(pdf_path).name
        pdf_image = np.array(page_image)
        detection_results = self.detect_text(pdf_image)
        
        if not detection_results or not detection_results[0]:
            self.logger.warning("No text detected on the PDF page.")
            return None
        
        boxes = [line[0] for line in detection_results[0]]
        texts = [line[1][0] for line in detection_results[0]]
        date_like_index = self.find_date_pattern(texts)
        text_box = boxes[date_like_index] if date_like_index is not None else None
        
        if text_box is None:
            return None
        else:
            x_min = int(min(point[0] for point in text_box))
            y_min = int(min(point[1] for point in text_box))
            x_max = int(max(point[0] for point in text_box))
            y_max = int(max(point[1] for point in text_box))
            line_image_np = pdf_image[y_min:y_max, x_min:x_max]
            if self.save_crop_img:
                self.save_image(line_image_np, self.save_folder, f"date_image_{file_name}_page_{page_num}.jpg")

            line_image = Image.fromarray(line_image_np)
            date_texts = self.img2text(line_image)
            date = self.extract_and_format_date(date_texts)
            if date:
                return date
            else:
                return "Blank date"
            