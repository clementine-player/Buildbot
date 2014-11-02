from trusty-i386

# apt-fast
run apt-get update
run apt-get install -y aria2
add apt-fast /bin/apt-fast

# Buildbot slave
run apt-fast install -y python-pip python-dev git
run pip install buildbot_slave

# Build tools
run apt-fast install -y yasm cmake qt4-dev-tools stow unzip autoconf libtool \
    bison flex pkg-config gettext libglib2.0-dev intltool wine git-core \
    sudo texinfo wget

# Install the old version of libtool
run wget -q -O /libtool.deb 'https://googledrive.com/host/0Byds9jlkR0IxbXVUa1Flb3h6bjQ/libtool_2.2.6b-2ubuntu1_i386.deb' && \
    dpkg -i /libtool.deb && \
    rm /libtool.deb

# Install the mingw toolchain and add it to the path
run wget -q -O /mingw.tar.bz2 'https://googledrive.com/host/0Byds9jlkR0IxbXVUa1Flb3h6bjQ/mingw-w32-bin_i686-linux_20130523.tar.bz2' && \
    mkdir /mingw && \
    tar -xvf /mingw.tar.bz2 -C /mingw && \
    rm /mingw.tar.bz2 && \
    ln -v -s /mingw/bin/* /bin/

# Create directories
run mkdir /usr/i586-mingw32msvc /usr/i586-mingw32msvc/stow /usr/i586-mingw32msvc/bin
run ln -s /usr/i586-mingw32msvc /target
run ln -s /mingw/i686-w64-mingw32/lib/libgcc_s_sjlj-1.dll /target/bin/
run ln -s /persistent-data/mingw/windows-dependencies/source /src

# Give the buildslave a name
run echo "mingw" > /slave-name
cmd ["/usr/bin/python", "/config/slave/start.py"]
