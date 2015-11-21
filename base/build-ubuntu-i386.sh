#!/bin/sh

if [ $# != 2 ]; then
  echo "Usage: $0 [ubuntu|debian] [precise|trusty|utopic|...]"
  exit 1
fi

set -e -x
TYPE=$1
DISTRO=$2
TEMP_DIR=$(mktemp -d)

case "${TYPE}" in
  ubuntu)
    MIRROR=${MIRROR:-http://archive.ubuntu.com/ubuntu/}
    ;;
  debian)
    MIRROR=${MIRROR:-http://httpredir.debian.org/debian/}
    ;;
  *)
    echo "Unknown type '${TYPE}'"
    exit 1
esac

debootstrap --variant=buildd \
            --arch i386 \
            "${DISTRO}" \
            "${TEMP_DIR}" \
            "${MIRROR}"

tar -C "${TEMP_DIR}" -c . | docker import - "${DISTRO}-i386-base"
sed "s/%DISTRO%/${DISTRO}/g" ubuntu.Dockerfile.template | \
  docker build -t "clementine/${TYPE}:${DISTRO}-i386" -
rm -rf "${TEMP_DIR}"

set +x
echo
echo "Done!  Upload this image to dockerhub with:"
echo
echo "  docker push clementine/${TYPE}:${DISTRO}-i386"
echo
