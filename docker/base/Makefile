all: push

push: build
	docker push clementine/ubuntu:precise-i386
	docker push clementine/ubuntu:trusty-i386
	docker push clementine/ubuntu:utopic-i386

build: build-precise-i386 build-trusty-i386 build-utopic-i386 build-fedora-20-i386 build-fedora-21-i386

build-precise-i386: precise-i386-base
	tar -C precise-i386-base -c . | docker import - precise-i386-base
	docker build -t clementine/ubuntu:precise-i386 precise-i386

build-trusty-i386: trusty-i386-base
	tar -C trusty-i386-base -c . | docker import - trusty-i386-base
	docker build -t clementine/ubuntu:trusty-i386 trusty-i386

build-utopic-i386: utopic-i386-base
	tar -C utopic-i386-base -c . | docker import - utopic-i386-base
	docker build -t clementine/ubuntu:utopic-i386 utopic-i386

precise-i386-base:
	debootstrap --variant=buildd --arch i386 precise precise-i386-base http://archive.ubuntu.com/ubuntu/

trusty-i386-base:
	debootstrap --variant=buildd --arch i386 trusty trusty-i386-base http://archive.ubuntu.com/ubuntu/

utopic-i386-base:
	debootstrap --variant=buildd --arch i386 utopic utopic-i386-base http://archive.ubuntu.com/ubuntu/

build-make-fedora-image:
	docker build -t make-fedora-image make-fedora-image

fedora-20-i386-base: build-make-fedora-image
	-mkdir fedora-images
	docker run -v $(shell pwd)/fedora-images:/data make-fedora-image 20

fedora-21-i386-base: build-make-fedora-image
	-mkdir fedora-images
	docker run -v $(shell pwd)/fedora-images:/data make-fedora-image 21

build-fedora-20-i386: fedora-20-i386-base
	tar -C fedora-images/fedora-20-i386 -c . | docker import - fedora-20-i386-base
	docker build -t clementine/fedora:20-i386 fedora-20-i386

build-fedora-21-i386: fedora-21-i386-base
	tar -C fedora-images/fedora-21-i386 -c . | docker import - fedora-21-i386-base
	docker build -t clementine/fedora:21-i386 fedora-21-i386

clean:
	rm -rf *-i386-base fedora-images
