from gcr.io/clementine-data/fedora:29-i386

run setarch i386 dnf install --assumeyes \
    buildbot-slave git tar rpmdevtools \
    gcc-c++ liblastfm-devel taglib-devel gettext boost-devel \
    qt-devel cmake gstreamer1-devel gstreamer1-plugins-base-devel glew-devel \
    libgpod-devel qjson-devel libplist-devel \
    libusbmuxd-devel libmtp-devel protobuf-devel protobuf-compiler qca-devel \
    libcdio-devel qca-ossl fftw-devel sparsehash-devel sqlite-devel \
    pulseaudio-libs-devel qtwebkit-devel sha2-devel desktop-file-utils \
    libechonest-devel libchromaprint-devel cryptopp-devel

run echo "fedora-29-32" > /slave-name

# Create the buildbot user.
run useradd -r -m -s /bin/false buildbot
run mkdir -p /home/buildbot/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS} && \
    chown buildbot /home/buildbot/rpmbuild/{,BUILD,RPMS,SOURCES,SPECS,SRPMS}
cmd ["/usr/bin/python", "/config/slave/start.py"]
entrypoint []
