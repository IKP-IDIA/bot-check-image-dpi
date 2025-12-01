import fitz  # PyMuPDF
import os
import subprocess
import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
import tempfile
from typing import Optional

# โฟลเดอร์ Input/Output
INPUT_DIR = "data"
OUTPUT_DIR = "output"
LIBREOFFICE_COMMAND = "libreoffice"

def is_pdf_by_extension(filepath):
    """ตรวจสอบว่าเป็นไฟล์ PDF จากนามสกุลไฟล์ (.pdf)"""
    # print(filepath)
    return str(filepath).lower().endswith('.pdf')


def convert_word_bytes_to_pdf(word_bytes: bytes , original_filename: str ) -> Optional[bytes]:
    """
    แปลง Word Bytes เป็น PDF Bytes โดยใช้ LibreOffice และจัดการไฟล์ชั่วคราว
    """
    try:
        # 1. สร้างโฟลเดอร์ชั่วคราวสำหรับ Input และ Output
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # --- ไฟล์ Input ---
            docx_input_filename = "input.docx"
            docx_temp_path = os.path.join(temp_dir, docx_input_filename)
            
            # 2. เขียน DOCX Bytes ลงไฟล์ชั่วคราว
            with open(docx_temp_path, "wb") as f:
                f.write(word_bytes)

            # --- 3. สั่งแปลงไฟล์ ---
            # สั่งให้สร้างไฟล์ PDF ใน temp_dir เดียวกัน
            cmd = [
                LIBREOFFICE_COMMAND,
                "--headless", 
                "--convert-to", "pdf",
                "--outdir", temp_dir, # ✅ แก้: สั่งให้ output ไปที่ temp_dir
                docx_temp_path
            ]
            
            result = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # --- 4. ตรวจสอบผลลัพธ์และอ่านไฟล์ ---
            
            if result.returncode == 0:
                # ชื่อไฟล์ที่ LibreOffice สร้างจะเป็นชื่อเดิม + นามสกุลใหม่: input.pdf
                pdf_output_filename = "input.pdf"
                pdf_output_path = os.path.join(temp_dir, pdf_output_filename)
                
                if not os.path.exists(pdf_output_path):
                     print(f"❌ ERROR: Conversion successful but output file not found at {pdf_output_path}")
                     print(f"LibreOffice Output: {result.stderr.decode()}")
                     return None
                
                # อ่านไฟล์ PDF กลับมาเป็น Bytes
                with open(pdf_output_path, "rb") as f:
                    pdf_output_bytes = f.read()
                    
                    
                # ##### SAVE TO LOACAL ############
                # # 6. ✅ บันทึกไฟล์ไปยังโฟลเดอร์ปลายทาง "output"
                # final_pdf_filename = os.path.splitext(original_filename)[0] + ".pdf"
                # final_path = os.path.join(OUTPUT_DIR, final_pdf_filename)

                # with open(final_path, "wb") as out_f:
                #     out_f.write(pdf_output_bytes)
                #     print(f"✅ File saved to disk: {final_path}")
                # ###############################################
                
                # ไฟล์ชั่วคราวจะถูกลบเมื่อออกจาก with block
                return pdf_output_bytes
            else:
                print(f"❌ Convert Error (Code {result.returncode}): {result.stderr.decode('utf-8')}")
                return None
                
    except FileNotFoundError:
        print("❌ Error: LibreOffice command not found. Is it installed and in the PATH?")
        return None
    except Exception as e:
        print(f"❌ Conversion Error: {e}")
        return None


def analyze_pdf_dpi(pdf_bytes):
    """
    วิเคราะห์และคำนวณหาค่า DPI จริงของรูปภาพที่ฝังอยู่ใน PDF
    สูตร: DPI = (Image Width Pixels / Display Width Inches)
    """
    try:
        dpi_x = None
        dpi_y = None
        status_dpi = None
        describe = None
        
        list_page = []
        
        # # เปิดไฟล์ PDF (รองรับ path ภาษาไทยได้ดีกว่า)
        # doc = fitz.open(pdf_path)
        # print(f"กำลังวิเคราะห์ไฟล์: {os.path.basename(pdf_path)}")
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        found_images = False
        list_page_fail = []
        describe = 'รูปมีขนาดมากกว่าเท่ากับ 300 dpi'
        status_dpi = "success"
        for page_num, page in enumerate(doc):
            # ดึงรายการรูปภาพทั้งหมดในหน้านั้น
            image_list = page.get_images(full=True)
            
            if image_list:
                print(f"\n--- หน้าที่ {page_num + 1} ---")
                found_images = True
            
            ###########################################################################################################
                largest_rects_on_page = []
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    rects = page.get_image_rects(xref)
                    
                    if rects:
                        # 2. เลือกเฉพาะ Rect ที่ใหญ่ที่สุดจากรายการ rects ของ xref นี้
                        # (r[2]-r[0])*(r[3]-r[1]) คือการคำนวณ Area (width * height)
                        largest_rect_for_this_xref = max(rects, 
                                                        key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
                        
                        largest_rects_on_page.append((xref, largest_rect_for_this_xref))
                        
            if largest_rects_on_page:
                final_largest_image_info = max(largest_rects_on_page, 
                                                key=lambda item: (item[1].x1 - item[1].x0) * (item[1].y1 - item[1].y0))
            ################################################################################################################                        
            # for img_index, img in enumerate(image_list):
                # xref = img[0] # รหัสอ้างอิงรูปภาพ
                xref = final_largest_image_info[0]
                
                # 1. ดึงข้อมูลรูปภาพดิบ (Raw Image)
                base_image = doc.extract_image(xref)
                raw_width = base_image["width"]
                raw_height = base_image["height"]
                ext = base_image["ext"]
                
                # 2. หาขนาดที่แสดงผลบนหน้ากระดาษ (Display Size)
                # get_image_rects จะบอกว่ารูปนี้ถูกวาดลงตรงไหนของหน้าบ้าง
                rects = page.get_image_rects(xref)
                print(rects)
                
                shape = page.new_shape()
                
                for rect in rects:
                    # PDF ใช้หน่วย Point (1 นิ้ว = 72 points)
                    # คำนวณความกว้างเป็นนิ้ว
                    width_inch = rect.width / 72.0
                    height_inch = rect.height / 72.0
                    
                    # 3. คำนวณ DPI
                    # DPI = Pixel / Inch
                    dpi_x = raw_width / width_inch
                    dpi_y = raw_height / height_inch
                    
                    # ปัดเศษให้ดูง่าย
                    dpi_val = int(min(dpi_x, dpi_y)) 
                    
                    print(f"    รูปที่ {img_index + 1} ({ext}):")
                    print(f"      - ขนาดดิบ: {raw_width} x {raw_height} px")
                    print(f"      - ขนาดบนเอกสาร: {width_inch:.2f} x {height_inch:.2f} นิ้ว")
                    print(f"      - DPI: {dpi_x} DPI x {dpi_y} DPI")
                    print(f"      - ✅ DPI ที่แท้จริง: {dpi_val} DPI")
                    
                    if dpi_val < 300:
                        print(f"เตือน: รูปนี้ความละเอียดต่ำกว่า 300 DPI\n")
                        describe = 'รูปมีขนาดน้อยกว่า 300 dpi'
                        status_dpi = "fail"
                        list_page_fail.append({"page": page_num + 1, "dpi_x": dpi_x, "dpi_y": dpi_y, })
                        
                    # color=(R, G, B) -> (1, 0, 0) คือสีแดง
                    shape.draw_rect(rect)
                    shape.finish(color=(1, 0, 0), width=2) # เส้นหนา 2
                    
                    # (Optional) เขียนข้อความกำกับว่า xref อะไร
                    shape.insert_text(rect.tl, f"Img: {xref}", color=(0, 0, 1), fontsize=10)
                    
                shape.commit()
    # แปลงหน้านั้นเป็นรูปภาพ (Render) เพื่อดูผลลัพธ์
                # matrix=fitz.Matrix(2, 2) คือขยาย 2 เท่าให้ภาพชัดขึ้น (Zoom 200%)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
                
                output_path = os.path.join("output_images", f"debug_page_{page_num+1}.png")
                # pix.save(output_path)
                
        if len(list_page_fail) > 0  :
            dpi_json_return = {"status": status_dpi, "describe": describe, "detail": list_page_fail}
        else:
            dpi_json_return = {"status": status_dpi, "describe": describe}
            
        if not found_images:
            print("\nℹ️ ไม่พบรูปภาพในไฟล์ PDF นี้ (อาจเป็นข้อความล้วน หรือ Vector)")
            dpi_json_return = {"status": "success", "describe": "ไม่พบรูปภาพในไฟล์"}
            # กรณีเป็น Vector/Text ล้วน ถือว่าคุณภาพสูงที่สุด (Infinite DPI)
            
        return dpi_json_return
            
    except Exception as e:
        print(f"Error analyzing PDF: {e}")

# # --- ทดสอบใช้งาน ---
# if __name__ == "__main__":
#     # ใส่ path ไฟล์ที่มีปัญหาของคุณลงไป
#     # pdf_file = "./data/งานจ้างพัฒนาระบบ New e-App (SMP) #1 req และโจทย์ POC.pdf" 
#     pdf_file = "./data/05_โครงสร้างองค์กร.pdf" 
    
#     if os.path.exists(pdf_file):
#         analyze_pdf_dpi(pdf_file)
#     else:
#         print("ไม่พบไฟล์")

# target_pdf = convert_to_pdf_linux("./data/02_ตัวอย่าง passport.docx", "./output")
# target_pdf = convert_to_pdf_linux("./data/01_คำรับรองของบุคคลที่ขอความเห็นชอบพิจารณา-ตรวจสอบ.docx", "./output")

def check_dpi(pdf_bytes, file_name):
    if is_pdf_by_extension(file_name):
        print("it's already pdf...")
        dpi_val  = analyze_pdf_dpi(pdf_bytes)
    else:
        print("it's not pdf converting to pdf...")
        target_pdf = convert_word_bytes_to_pdf(pdf_bytes, file_name)
        if target_pdf:
            dpi_val = analyze_pdf_dpi(target_pdf)
            
    print("\n")
    return dpi_val