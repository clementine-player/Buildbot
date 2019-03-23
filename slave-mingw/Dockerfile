from i386/ubuntu:xenial

run echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections

run apt-get update && apt-get install -y \
    # Buildbot slave
    python-pip python-dev git \
    # Build tools
    yasm cmake qt4-dev-tools stow unzip autoconf libtool \
    bison flex pkg-config gettext libglib2.0-dev intltool wine git-core \
    sudo texinfo wget nsis \
    protobuf-compiler \
    mingw-w64

run pip install buildbot_slave

# Install the old version of libtool
run wget -q -O /libtool.deb 'https://storage.googleapis.com/clementine-data.appspot.com/Build%20dependencies/libtool_2.2.6b-2ubuntu1_i386.deb' && \
    dpkg -i /libtool.deb && \
    rm /libtool.deb

# Work around https://github.com/docker/docker/issues/6047
run rm -rf /root && mkdir /root --mode 0755

# Give the buildslave a name
run echo "mingw" > /slave-name

# Create the buildbot user.
run useradd -r -m -s /bin/false buildbot
cmd ["/usr/bin/python", "/config/slave/start.py"]

run mkdir -p /target/stow

run git clone https://github.com/clementine-player/Dependencies.git /src
run cd /src/windows && make all-downloads
copy Makefile /src/windows/Makefile
run cd /src/windows && make
