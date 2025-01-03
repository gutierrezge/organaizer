FROM nvidia/cuda:12.3.1-runtime-ubuntu22.04

# Set the working directory
WORKDIR /workspace

# Disable interactive mode
ENV DEBIAN_FRONTEND=noninteractive

# Install OS dependencies
RUN apt update && apt -y upgrade && apt -y autoremove
RUN apt install -y build-essential software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update && apt -y upgrade && apt -y autoremove
RUN apt install -y git wget curl unzip tar zip libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev python3.12 python3-pip

# # Update python dependencies
RUN pip3 install --upgrade pip
RUN pip install jupyter opencv-python pandas numpy matplotlib seaborn scikit-learn ultralytics

# Run jupyter using python enviroment when container starts
CMD jupyter notebook --allow-root --ip=0.0.0.0