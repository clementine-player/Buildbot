all: push

push: build
	docker push clementine/ubuntu:precise-i386
	docker push clementine/ubuntu:trusty-i386
	docker push clementine/ubuntu:utopic-i386

build: build-precise-i386 build-trusty-i386 build-utopic-i386

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

clean:
	rm -rf *-i386-base
