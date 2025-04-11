FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip==24.0 && \
    pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt

# Copy application files
COPY . .

# Create directory for pretrained models and download model checkpoints
RUN mkdir -p pretrained && \
    cd pretrained && \
    # Download SOMEv0.0.1 model
    wget -q https://github.com/openvpi/SOME/releases/download/v0.0.1/0918_continuous256_clean_3spk_fixmel.zip && \
    unzip 0918_continuous256_clean_3spk_fixmel.zip && \
    rm 0918_continuous256_clean_3spk_fixmel.zip && \
    # Download SOMEv1 model
    wget -q https://github.com/openvpi/SOME/releases/download/v1.0.0-baseline/0119_continuous128_5spk.zip && \
    unzip 0119_continuous128_5spk.zip && \
    rm 0119_continuous128_5spk.zip && \
    # Download RMVPE model
    wget -q https://github.com/yxlllc/RMVPE/releases/download/v1.0.5/rmvpe.pt

# Add volume mount points for input and output files
VOLUME ["/app/input", "/app/output"]

# Set entrypoint to run inference
ENTRYPOINT ["python", "infer.py"]

# Default command (can be overridden)
CMD ["--help"] 