# Use a base image that supports multiple architectures
FROM --platform=linux/amd64 python:3.8-slim as build-x86_64

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1

# Copy files necessary for the build
COPY finch-project-399922-0196b8dd1667.json .
COPY requirements.txt .
COPY Sprint3/calib_img.png .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY birdsv3.py .

# Use a base image for ARM architecture (like Raspberry Pi)
FROM --platform=linux/arm/v7 python:3.8-slim as build-arm

WORKDIR /app

# Repeat the steps for ARM architecture
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

# Final stage: decide which build to use based on the target platform
FROM build-${TARGETARCH}

CMD ["python", "birdsv3.py"]
