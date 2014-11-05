COMMON_ARGS=-v $(shell pwd)/config:/config --volumes-from volumes
MASTER_ARGS=${COMMON_ARGS} -p 8010:8010 
SLAVE_ARGS=${COMMON_ARGS} --link master:master

all:
	@echo "Controlling Docker images and containers:"
	@echo "  make build           Creates the images: only do this once"
	@echo "  make start           Starts master and slaves"
	@echo "  make stop            Stops master and slaves, destroys containers"
	@echo "  make restart         Restarts master and slaves"
	@echo
	@echo "Debugging:"
	@echo "  make debug           Outputs the master's log file so you can see what broke"
	@echo "  make data            Starts a shell in the shared volume container"
	@echo "  make delete-volumes  Deletes the shared volume container, recreate with 'make start'"

build:
	docker build -t clementine-buildbot-master master
	docker build -t clementine-buildbot-volumes volumes
	docker build -t clementine-buildbot-slave-precise slave-precise
	docker build -t clementine-buildbot-slave-trusty slave-trusty
	docker build -t clementine-buildbot-slave-utopic slave-utopic
	docker build -t clementine-buildbot-slave-mingw slave-mingw

trusty-i386-root:
	debootstrap --variant=buildd --arch i386 trusty tmp-trusty-i386-root http://archive.ubuntu.com/ubuntu/
	mv tmp-trusty-i386-root trusty-i386-root

mingw-base: trusty-i386-root
	tar -C trusty-i386-root -c . | docker import - trusty-i386-base

start: start-volumes
	docker run -d ${MASTER_ARGS} --name master clementine-buildbot-master
	docker run -d ${SLAVE_ARGS} --name slave-precise clementine-buildbot-slave-precise
	docker run -d ${SLAVE_ARGS} --name slave-trusty clementine-buildbot-slave-trusty
	docker run -d ${SLAVE_ARGS} --name slave-utopic clementine-buildbot-slave-utopic
	docker run -d ${SLAVE_ARGS} --name slave-mingw clementine-buildbot-slave-mingw

start-volumes:
	@docker inspect -f "Volume container already created" volumes 2>/dev/null \
		|| docker run -d --name volumes clementine-buildbot-volumes

stop: 
	-for container in master slave-precise slave-trusty slave-utopic slave-mingw; do \
		docker stop $${container}; \
		docker rm $${container}; \
	done

delete-volumes:
	docker rm volumes

restart: stop start

debug:
	docker run ${MASTER_ARGS} clementine-buildbot-master --debug

data:
	docker run ${COMMON_ARGS} -t -i ubuntu

register-wine:
	mount binfmt_misc -t binfmt_misc /proc/sys/fs/binfmt_misc 
	echo ':DOSWin:M::MZ::/usr/bin/wine:' > /proc/sys/fs/binfmt_misc/register
