FROM osrf/ros:jazzy-desktop-full

# SETUP ENVS
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV color_prompt=yes
ENV DEBIAN_FRONTEND noninteractive
ENV NVIDIA_VISIBLE_DEVICES ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics

# SETUP parallel workers
ARG parallel_workers=1

# INSTALL SOME ESSENTIAL PROGRAMS
RUN apt update
RUN apt install -y    \
        git wget bash-completion unzip python3-pip python3-venv python3-catkin-pkg-modules

RUN mkdir -p /AS_ws/src
WORKDIR /AS_ws
RUN python3 -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip

# make sure scripts use the venv by adjusting PATH
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /AS_ws
RUN mkdir rendered
WORKDIR /AS_ws/src
RUN git clone https://github.com/MaciejBr01/depth_simulation_publisher.git
WORKDIR /AS_ws/src/depth_simulation_publisher
RUN git submodule update --init
RUN pip install -r requirements.txt
WORKDIR /AS_ws
RUN /bin/bash -c ". /opt/ros/jazzy/setup.bash; colcon build --parallel-workers $parallel_workers"

WORKDIR /AS_ws


RUN ldconfig


# FILL BASHRC
WORKDIR /AS_ws
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc
RUN echo "source /AS_ws/install/setup.bash" >> ~/.bashrc
