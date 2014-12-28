from fedora-20-i386-base

run rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-i386
run rm -rf /usr/lib/locale/locale-archive /var/cache/yum/*

entrypoint ["/bin/setarch", "i386"]
