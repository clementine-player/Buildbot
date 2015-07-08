from ubuntu:precise

# Buildbot slave
run apt-get update && apt-get install -y python-pip python-dev git
run pip install buildbot_slave

# Gstreamer developers PPA (required on Precise for gstreamer-1.0)
run apt-get install -y python-software-properties
run add-apt-repository ppa:gstreamer-developers/ppa
run apt-get update

# Clementine dependencies
run apt-get update && apt-get install -y \
    liblastfm-dev libtag1-dev gettext libboost-dev \
    libboost-serialization-dev libqt4-dev qt4-dev-tools libqt4-opengl-dev \
    cmake libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    libglew1.5-dev libqjson-dev libgpod-dev libplist-dev \
    libusbmuxd-dev libmtp-dev libcdio-dev \
    protobuf-compiler libprotobuf-dev libqca2-dev libqca2-plugin-ossl \
    libfftw3-dev libsparsehash-dev libsqlite3-dev libpulse-dev \
    libqtwebkit-dev
run apt-get update && apt-get install -y libcrypto++-dev libchromaprint-dev
run apt-get update && apt-get install -y libechonest-dev

# Give the buildslave a name
run echo "precise-64" > /slave-name
cmd ["/usr/bin/python", "/config/slave/start.py"]
