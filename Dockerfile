FROM roboflow/roboflow-inference-server-gpu:latest

RUN apt-get update && \
    apt-get install -y python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade --force-reinstall \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cu130