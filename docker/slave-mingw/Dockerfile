from clementine/ubuntu:trusty-i386

# apt-fast
run apt-get update && apt-get install -y aria2
add apt-fast /bin/apt-fast

# Buildbot slave
run apt-fast install -y python-pip python-dev git
run pip install buildbot_slave

# Build tools
run apt-fast install -y yasm cmake qt4-dev-tools stow unzip autoconf libtool \
    bison flex pkg-config gettext libglib2.0-dev intltool wine git-core \
    sudo texinfo wget nsis

# Install the old version of libtool
run wget -q -O /libtool.deb 'https://googledrive.com/host/0Byds9jlkR0IxbXVUa1Flb3h6bjQ/libtool_2.2.6b-2ubuntu1_i386.deb' && \
    dpkg -i /libtool.deb && \
    rm /libtool.deb

# Install the mingw toolchain and add it to the path
run wget --progress=dot:mega -O /mingw.tar.bz2 \
      'https://googledrive.com/host/0Byds9jlkR0IxbXVUa1Flb3h6bjQ/mingw-w32-bin_i686-linux_20130523.tar.bz2' && \
    mkdir /mingw && \
    tar -xvf /mingw.tar.bz2 -C /mingw && \
    rm /mingw.tar.bz2 && \
    ln -v -s /mingw/bin/* /bin/ && \
    find /mingw -executable -exec chmod go+rx {} ';' && \
    find /mingw -readable -exec chmod go+r {} ';'

# Work around https://github.com/docker/docker/issues/6047
run rm -rf /root && mkdir /root --mode 0755

add slave-mingw/first-time-setup.sh /first-time-setup.sh
run ln -s /persistent-data/mingw/target /target
run ln -s /persistent-data/mingw/target /usr/i586-mingw32msvc
run ln -s /persistent-data/mingw/windows-dependencies/source /src

# Give the buildslave a name
run echo "mingw" > /slave-name

# Create the buildbot user.
run useradd -r -m -s /bin/false buildbot
cmd ["/usr/bin/python", "/config/slave/start.py"]
