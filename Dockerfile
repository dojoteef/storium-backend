FROM python:3.7

#**********************************************************************************************************************************************#
# Unfortunately, there isn't an easy way to combine the python docker images with the NVIDIA CUDA images, so I copy the CUDA docker file
# commands into this Dockerfile
#**********************************************************************************************************************************************#

################################################################################################################################################
# Taken from https://gitlab.com/nvidia/container-images/cuda/blob/c8f0a52e621b314df4acb8f33e6a77d704c493dc/dist/ubuntu18.04/10.1/base/Dockerfile
################################################################################################################################################
RUN apt-get update && apt-get install -y --no-install-recommends \
gnupg2 curl ca-certificates && \
    curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub | apt-key add - && \
    echo "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64 /" > /etc/apt/sources.list.d/cuda.list && \
    echo "deb https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64 /" > /etc/apt/sources.list.d/nvidia-ml.list && \
    apt-get purge --autoremove -y curl && \
rm -rf /var/lib/apt/lists/*

ENV CUDA_VERSION 10.1.243

ENV CUDA_PKG_VERSION 10-1=$CUDA_VERSION-1

# For libraries in the cuda-compat-* package: https://docs.nvidia.com/cuda/eula/index.html#attachment-a
RUN apt-get update && apt-get install -y --no-install-recommends \
        cuda-cudart-$CUDA_PKG_VERSION \
cuda-compat-10-1 && \
ln -s cuda-10.1 /usr/local/cuda && \
    rm -rf /var/lib/apt/lists/*

# Required for nvidia-docker v1
RUN echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf && \
    echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf

ENV PATH /usr/local/nvidia/bin:/usr/local/cuda/bin:${PATH}
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64

# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility
ENV NVIDIA_REQUIRE_CUDA "cuda>=10.1 brand=tesla,driver>=384,driver<385 brand=tesla,driver>=396,driver<397 brand=tesla,driver>=410,driver<411"

###################################################################################################################################################
# Taken from https://gitlab.com/nvidia/container-images/cuda/blob/c8f0a52e621b314df4acb8f33e6a77d704c493dc/dist/ubuntu18.04/10.1/runtime/Dockerfile
###################################################################################################################################################
ENV NCCL_VERSION 2.4.8

RUN apt-get update && apt-get install -y --no-install-recommends \
    cuda-libraries-$CUDA_PKG_VERSION \
cuda-nvtx-$CUDA_PKG_VERSION \
libnccl2=$NCCL_VERSION-1+cuda10.1 && \
    apt-mark hold libnccl2 && \
    rm -rf /var/lib/apt/lists/*

##########################################################################################################################################################
# Taken from https://gitlab.com/nvidia/container-images/cuda/blob/87fa7bc298427768de09500820ae1964862126a1/dist/ubuntu18.04/10.1/runtime/cudnn7/Dockerfile
##########################################################################################################################################################
ENV CUDNN_VERSION 7.6.4.38
LABEL com.nvidia.cudnn.version="${CUDNN_VERSION}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcudnn7=$CUDNN_VERSION-1+cuda10.1 \
&& \
    apt-mark hold libcudnn7 && \
    rm -rf /var/lib/apt/lists/*

#####################################
# Figmentator specific commands below
#####################################
ARG PIP_CMD="pip3 install"

# Copy the files needed to build the app
WORKDIR /var/www/figmentator
COPY setup.py ./
COPY src src
COPY scripts scripts

# # Install build dependencies, then install app, then remove build dependencies
# RUN apk add --no-cache --virtual .build-deps gcc libc-dev make \
#       && $PIP_CMD .[redis] && apk del .build-deps gcc libc-dev make \
#       && rm -rf setup.py src scripts
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip \
      && $PIP_CMD .[redis] && rm -rf /var/lib/apt/lists/*

# Create a user and group that actually run the app, so we aren't running as root
RUN addgroup --system fig && adduser --system fig --ingroup fig --home /home/fig

# Create a location for the model installation
RUN mkdir /var/lib/figmentator && chown fig:fig /var/lib/figmentator

# Tell docker that all future commands should run as the fig user
USER fig
CMD figment
