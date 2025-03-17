# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Gabriel Gutierrez Anez

FROM ultralytics/ultralytics:latest

# Disable interactive mode
ENV DEBIAN_FRONTEND=noninteractive

# Ensures NVIDIA GPUs are available
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

# Install OS dependencies
RUN apt update && apt -y upgrade && apt -y autoremove
RUN apt install -y \
    libusb-1.0-0-dev \
    usbutils \
    xclip \
    libmtdev1

# Update python dependencies
RUN pip install --upgrade pip
RUN pip install \
    py3dbp \
    kivymd \
    sqlalchemy \
    psycopg2-binary \
    pyrealsense2 \
    scikit-image \
    scikit-learn \
    python-dotenv \
    PyWavelets

# Set workdir back to normal
WORKDIR /app

# Run jupyter using python enviroment when container starts
CMD python3 app.py
