# ใช้ Python 3.10 แบบตัวเล็ก (Slim)
FROM python:3.10-slim

# ตั้งค่า Environment ไม่ให้ถาม confirm เวลาลงของ
ENV DEBIAN_FRONTEND=noninteractive

# 1. ติดตั้ง System Dependencies
# - libreoffice: แทน MS Office
# - poppler-utils: สำหรับ pdf2image
# - fonts-thai-tlwg: ฟอนต์ไทย (สำคัญมาก ไม่งั้นอ่านไม่ออก)
RUN apt-get update && apt-get install -y \
    libreoffice \
    poppler-utils \
    fonts-thai-tlwg \
    && rm -rf /var/lib/apt/lists/*

# 2. ตั้งค่า Work Directory
WORKDIR /app

# 3. Copy และ Install Python Libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy โค้ดทั้งหมด
COPY . .

# 5. คำสั่งรัน
CMD ["python", "main.py"]