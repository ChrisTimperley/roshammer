INDIGO=laser_proc \
       imu_transformer \
       depthimage_to_laserscan \
       pointcloud_to_laserscan

all: $(INDIGO)

$(INDIGO):
	docker build \
	  --build-arg DISTRO=indigo \
	  --build-arg PACKAGE=$@ \
	  -t roshammer/$@ .

.PHONY: $(INDIGO)
