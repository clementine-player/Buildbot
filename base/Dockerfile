ARG DISTRO
from gcr.io/clementine-data/fedora-${DISTRO}-i386-base
ARG DISTRO

run rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-${DISTRO}-i386
run rm -rf /usr/lib/locale/locale-archive /var/cache/yum/*

entrypoint ["/bin/setarch", "i386"]
