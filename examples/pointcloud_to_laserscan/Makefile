all: pointcloud_to_laserscan

pointcloud_to_laserscan:
	docker build \
	  --build-arg DISTRO=kinetic \
	  --build-arg PACKAGE=pointcloud_to_laserscan \
	  -t roshammer/pointcloud_to_laserscan .

.PHONY: pointcloud_to_laserscan
