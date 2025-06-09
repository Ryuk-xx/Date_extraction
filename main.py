import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File
import uvicorn
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from source.models.pipeline import PipelineExtractor
from config.logging_config import setup_logging
from config.config import load_config
from db.db import Database_logs

DB_LOG = Database_logs()
# Initialize the logger
logger = setup_logging()  
# Initialize the config
config = load_config()

temp_folder_path = config['sys']['temp_extract_path']
os.makedirs(temp_folder_path, exist_ok=True)
save_img_path = config['sys']['save_img_path']
max_pdf_pages = config['sys']['max_pdf_pages']

app = FastAPI()

pipeline = PipelineExtractor(
    max_pdf_pages = max_pdf_pages
)


@app.post("/contract")
async def extract_date(file: UploadFile = File(...)):
    current_date_folder = datetime.now().strftime('%Y-%m-%d')

    date_folder_path = os.path.join(temp_folder_path, current_date_folder)
    os.makedirs(date_folder_path, exist_ok=True) 
    temp_file_path = os.path.join(date_folder_path, file.filename)

    results = {"status_code": 200, "data": None, "message": "", "time_taken": ""}
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        logger.info(f"Received file for date extraction: {file.filename}, saving to {temp_file_path}")

        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        start = time.time()

        # Check file type and handle .doc conversion
        file_type = pipeline.check_file_type(temp_file_path)
        original_doc_path = temp_file_path

        if file_type == "doc":
            try:
                temp_file_path = pipeline.convert_doc_to_docx(original_doc_path)

                # Delete the original .doc file after conversion
                if original_doc_path and os.path.exists(original_doc_path):
                    os.remove(original_doc_path)
                    
                logger.info(f"Successfully converted .doc to .docx: {temp_file_path}")
            except Exception as e:
                logger.error(f"Failed to convert .doc to .docx: {e}")
                raise ValueError(f"Failed to convert .doc to .docx: {e}")
        
        date = pipeline.extract_date(temp_file_path)
        
        # if file_type not in ["pdf", "docx"]:
        #     raise ValueError("Unsupported file type. Only PDF and DOCX are allowed.")

       
        end = time.time()
        results["time_taken"] = f"{end - start:.2f}s"

        if date:
            results["data"] = date
            results["message"] = "Trích xuất ngày ký hợp đồng thành công!"
        else:
            results["status_code"] = 201
            results["message"] = "Không tìm thấy ngày ký hợp đồng trong văn bản!"

        # Thêm lời gọi save to postgres
        logger.info("DATE: {}".format(results["data"]))
        DB_LOG.save_logs(
            file_path=temp_file_path,
            request_time=request_time,
            run_time=results["time_taken"],
            status_code=results["status_code"],
            output=results["message"],
            extracted_date=results["data"],
        )
        return results

    except ValueError as ve:
        results["status_code"] = 400
        results["message"] = str(ve)
        logger.error(f"Validation error: {str(ve)}")
        DB_LOG.save_logs(
            file_path=temp_file_path,
            request_time=request_time,
            run_time="N/A",
            status_code=400,
            output=results["message"],
            extracted_date=None
        )
        raise HTTPException(status_code=400, detail=results["message"])

    except Exception as e:
        results["status_code"] = 500
        results["message"] = f"Có lỗi xảy ra: {str(e)}"
        logger.error(f"Error during date extraction: {str(e)}")
        DB_LOG.save_logs(
            file_path=temp_file_path,
            request_time=request_time,
            run_time="N/A", 
            status_code=500,
            output=results["message"],
            extracted_date=None
        )
        raise HTTPException(status_code=500, detail=results["message"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7007)

