from fedora:latest

run yum install -y yum-utils

add make-base-image.sh /

volume /data

entrypoint ["/bin/setarch", "i386", "/bin/sh", "/make-base-image.sh"]
cmd ["20"]
