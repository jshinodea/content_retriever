# Use CUDA base image for GPU support
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set Python environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Clone the repository
RUN git clone https://github.com/jshinodea/content_retriever.git .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose required ports
EXPOSE 8000
EXPOSE 9042
EXPOSE 6379

# Set the entrypoint
ENTRYPOINT ["python3"]
CMD ["src/main.py"] 