This directory contains Docker images for Clementine's buildbot.

Containers
==========

- `master`:
    Runs the buildbot master on port 8010.  This port is also exposed on the host
    machine.  All slaves connect to the master internally through docker over
    port 9989.

- `volumes`:
    Data-only container that holds persistent state for the master and all the
    slaves.  This is exposed as the /persistent-data directory in every
    container.

- `slave-*`:
    Every supported distro has its own container that runs its own buildbot
    slave.  The container has all the packages required to build Clementine.


Containers are built, started and stopped with decking.

1. First install decking and build the containers:

  ```
  npm install -g decking
  decking build all
  decking create
  ```

2. Then you can start and stop buildbot:

  ```
  decking start
  decking stop
  decking status
  decking restart
  ```

3. The master is then accessible on http://localhost:8010/.


Adding new slaves
=================

Replace `vivid` and `22` with the name of the Ubuntu distro or fedora version
that you want to add.

1. Create the i386 base images:

  ```
  cd base
  ./build-ubuntu-i386.sh vivid
  ./build-fedora-i386.sh 22
  ```

2. Create the `slave-vivid-32`, `slave-vivid-64`, `slave-fedora-22-32` and
   `slave-fedora-22-64` directories by copying from the last distro version and
   editing the two distro names in the `Dockerfile`

3. Add the images and containers to `decking.json`

4. Add the slaves and builders to `config/master/master.cfg.py`

5. Add passwords for the slaves to `config/passwords.py` and
   `config/passwords.py.example`

6. Build the images and containers and start the slaves:

  ```
  decking build all
  decking create
  decking start
  ```

7. See the builders on http://localhost:8010/builders.
