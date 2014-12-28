from clementine/fedora:21-i386

run setarch i386 yum install --assumeyes \
    buildbot-slave git tar rpmdevtools \
    gcc-c++ liblastfm-devel taglib-devel gettext boost-devel \
    qt-devel cmake gstreamer1-devel gstreamer1-plugins-base-devel glew-devel \
    libgpod-devel qjson-devel libplist-devel \
    usbmuxd-devel libmtp-devel protobuf-devel protobuf-compiler qca2-devel \
    libcdio-devel qca-ossl fftw-devel sparsehash-devel sqlite-devel \
    pulseaudio-libs-devel libqtwebkit-dev sha2-devel desktop-file-utils

run rpmdev-setuptree

run echo "fedora-21-32" > /slave-name
cmd ["/usr/bin/python", "/config/slave/start.py"]
