from ubuntu:xenial

run apt-get update && apt-get install -y \
    # Buildbot slave
    python-pip python-dev git \
    # Clementine dependencies
    liblastfm-dev libtag1-dev gettext libboost-dev libboost-serialization-dev \
    libqt4-dev qt4-dev-tools libqt4-opengl-dev \
    cmake libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    libglew1.5-dev libqjson-dev libgpod-dev libplist-dev \
    libusbmuxd-dev libmtp-dev libcdio-dev \
    protobuf-compiler libprotobuf-dev libqca2-dev libqca2-plugin-ossl \
    libfftw3-dev libsparsehash-dev libsqlite3-dev libpulse-dev \
    libqtwebkit-dev libcrypto++-dev libchromaprint-dev libechonest-dev \
    libcdio-cdda1 libmygpo-qt-dev \
    # Fakeroot is missing from the base package
    fakeroot

run pip install buildbot_slave

# Give the buildslave a name
run echo "ubuntu-xenial-64" > /slave-name

# Create the buildbot user.
run useradd -r -m -s /bin/false buildbot
cmd ["/usr/bin/python", "/config/slave/start.py"]
