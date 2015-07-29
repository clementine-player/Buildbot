from ubuntu:trusty

# Buildbot slave
run apt-get update && apt-get install -y python-pip python-dev git
run pip install buildbot_slave

# Clementine dependencies
run apt-get update && apt-get install -y \
    liblastfm-dev libtag1-dev gettext libboost-dev libboost-serialization-dev \
    libqt4-dev qt4-dev-tools libqt4-opengl-dev \
    cmake libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    libglew1.5-dev libqjson-dev libgpod-dev libplist-dev \
    libusbmuxd-dev libmtp-dev libcdio-dev \
    protobuf-compiler libprotobuf-dev libqca2-dev libqca2-plugin-ossl \
    libfftw3-dev libsparsehash-dev libsqlite3-dev libpulse-dev \
    libqtwebkit-dev libcrypto++-dev libchromaprint-dev libechonest-dev

# libspotify.
add https://developer.spotify.com/download/libspotify/libspotify-12.1.51-Linux-x86_64-release.tar.gz /src/
run cd /src && tar -xf libspotify-12.1.51-Linux-x86_64-release.tar.gz
run cd /src/libspotify-12.1.51-Linux-x86_64-release && make install
    
# Give the buildslave a name
run echo "spotify-blob-64" > /slave-name

# Create the buildbot user.
run useradd -r -m -s /bin/false buildbot
cmd ["/usr/bin/python", "/config/slave/start.py"]
