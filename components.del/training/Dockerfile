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
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

# Install OS dependencies
RUN apt update && apt -y upgrade && apt -y autoremove
RUN apt install -y libusb-1.0-0-dev usbutils xclip libmtdev1

# Update python dependencies
RUN pip install --upgrade pip
RUN pip install jupyter pyrealsense2 scikit-image scikit-learn python-dotenv PyWavelets matplotlib

# Set workdir back to normal
WORKDIR /workspace

# Run jupyter using python enviroment when container starts
CMD jupyter notebook