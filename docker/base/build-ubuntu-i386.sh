#!/bin/sh

if [ $# != 1 ]; then
  echo "Usage: $0 [precise|trusty|utopic|...]"
  exit 1
fi

set -e -x
DISTRO=$1
TEMP_DIR=$(mktemp -d)

debootstrap --variant=buildd \
            --arch i386 \
            "${DISTRO}" \
            "${TEMP_DIR}" \
            http://archive.ubuntu.com/ubuntu/

tar -C "${TEMP_DIR}" -c . | docker import - "${DISTRO}-i386-base"
sed "s/%DISTRO%/${DISTRO}/g" ubuntu.Dockerfile.template | \
  docker build -t "clementine/ubuntu:${DISTRO}-i386" -
rm -rf "${TEMP_DIR}"

set +x
echo
echo "Done!  Upload this image to dockerhub with:"
echo
echo "  docker push clementine/ubuntu:${DISTRO}-i386"
echo
