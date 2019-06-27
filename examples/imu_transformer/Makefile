all: imu_transformer

imu_transformer:
	docker build \
	  --build-arg DISTRO=indigo \
	  --build-arg PACKAGE=imu_transformer \
	  -t roshammer/imu_transformer .

.PHONY: imu_transformer
