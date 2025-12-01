from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from pydantic import BaseModel, Json
import shutil
import os
import core.check_image
import uvicorn
import json
from typing import List 

app = FastAPI()

# 1. สร้าง Pydantic Model สำหรับ JSON Data ที่จะรับเข้ามา
class DocumentMetadata(BaseModel):
    user_id: int
    doc_type: str
    tags: list[str]

@app.post("/upload")
async def upload_pdf_with_json(
    # รับไฟล์ PDF
    # file: UploadFile = File(...),
    files: List[UploadFile] = File(...),
    
    # รับ JSON Data (ใช้ Json[...] เพื่อให้ FastAPI แปลง string เป็น Dict/Model)
    metadata: str = Form(...) # <--- 1. รับเป็น String ธรรมดาก่อน
):
    try:
        print(f"metadata: {metadata}")
        
        # 2. แปลง String เป็น Dict ด้วย json.loads
        metadata_dict = json.loads(metadata)
        
        # 3. (Optional) Validate ด้วย Pydantic Model อีกที
        metadata_obj = DocumentMetadata(**metadata_dict)
        
        # # --- 2. เข้าถึงข้อมูล JSON ---
        # ตอนนี้ metadata กลายเป็น Object python ปกติแล้ว
        print(f"User ID: {metadata_obj.user_id}") 
        print(f"Doc Type: {metadata_obj.doc_type}")
        print(f"Tags: {metadata_obj.tags}")
        
        
        list_output = []
        for file in files:
            # --- 1. ตรวจสอบไฟล์ ---
            # if file.content_type != "application/pdf":
            #     raise HTTPException(status_code=400, detail="Only PDF files are allowed")

            file_name = file.filename

            # file_name
            print(f"files name: {file_name}")
            
            # do the function
            pdf_bytes = file.file.read()
            result_dpi_json = core.check_image.check_dpi(pdf_bytes, file_name)
            
            # output
            output_json = {"filename": file_name,
                            "received_metadata": metadata_obj, # ส่งกลับไปให้ดูเพื่อยืนยัน
                            "status": "success",
                            "dpi": result_dpi_json
                            }
            
            list_output.append(output_json)
            
    

        return list_output

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=5000)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        # workers=100,  # จำนวน worker processes
        # reload=False
    )