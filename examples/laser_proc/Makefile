all: laser_proc

laser_proc:
	docker build \
	  --build-arg DISTRO=indigo \
	  --build-arg PACKAGE=laser_proc \
	  -t roshammer/laser_proc .

.PHONY: laser_proc
