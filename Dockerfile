FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1
COPY finch-project-399922-0196b8dd1667.json .
COPY requirements.txt .
COPY Sprint3/calib_img.png . 

RUN pip install --no-cache-dir -r requirements.txt

COPY birdsv3.py .

CMD ["python", "birdsv3.py"]
