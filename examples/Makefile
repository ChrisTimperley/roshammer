INDIGO=laser_proc \
       image_rotate \
       imu_transformer \
       depthimage_to_laserscan \
       pointcloud_to_laserscan \
       face_detector \
       leg_detector

KINETIC=heron_control

all: $(INDIGO) $(KINETIC)

$(INDIGO):
	docker build \
	  --build-arg DISTRO=indigo \
	  --build-arg PACKAGE=$@ \
	  -t roshammer/$@ .

$(KINETIC):
	docker build \
	  --build-arg DISTRO=kinetic \
	  --build-arg PACKAGE=$@ \
	  -t roshammer/$@ .

.PHONY: $(INDIGO) $(KINETIC)
