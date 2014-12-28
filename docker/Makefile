COMMON_ARGS=-v $(shell pwd)/config:/config --volumes-from volumes
MASTER_ARGS=${COMMON_ARGS} -p 8010:8010 
SLAVE_ARGS=${COMMON_ARGS} --link master:master

SLAVES=mingw precise-32 precise-64 trusty-32 trusty-64 utopic-32 utopic-64 fedora-20-32 fedora-20-64 fedora-21-32 fedora-21-64

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
	docker build -t clementine/master master
	docker build -t clementine/volumes volumes

	for slave in ${SLAVES}; do \
		docker build -t clementine/slave:$${slave} slave-$${slave} || exit 1; \
	done

start: start-volumes
	docker run -d ${MASTER_ARGS} --name master clementine/master

	for slave in ${SLAVES}; do \
		docker run -d ${SLAVE_ARGS} --name slave-$${slave} clementine/slave:$${slave}; \
	done

start-volumes:
	@docker inspect -f "Volume container already created" volumes 2>/dev/null \
		|| docker run -d --name volumes clementine/volumes

stop:
	-docker stop master
	-docker rm master

	-for slave in ${SLAVES}; do \
		docker stop slave-$${slave}; \
		docker rm slave-$${slave}; \
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
