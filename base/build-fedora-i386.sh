#!/bin/sh

if [ $# != 1 ]; then
  echo "Usage: $0 [20|21|22|...]"
  exit 1
fi

set -e -x
DISTRO=$1
TEMP_DIR=$(mktemp -d)

docker build -t make-fedora-image make-fedora-image
docker run -v "${TEMP_DIR}:/data" make-fedora-image "${DISTRO}"
tar -C "${TEMP_DIR}/fedora-${DISTRO}-i386" -c . | \
  docker import - "gcr.io/clementine-data/fedora-${DISTRO}-i386-base"
sed "s/%DISTRO%/${DISTRO}/g" fedora.Dockerfile.template | \
  docker build -t "gcr.io/clementine-data/fedora:${DISTRO}-i386" -

set +x
echo
echo "Done!  Upload this image to dockerhub with:"
echo
echo "  docker push clementine/fedora:${DISTRO}-i386"
echo
