xhost +local:root

# BUILD THE IMAGE
ROS_IMAGE="as_proj"
if [ -z "$1" ]
	then
		echo "RUNNING WITH 1 WORKER"
		WORKERS=1
	else
		echo "RUNNING WITH $1 WORKERS"
		WORKERS=$1
fi
docker build -f Dockerfile --build-arg parallel_workers=$WORKERS -t $ROS_IMAGE ./..
