#!/bin/sh -e

DIST=lucid
PPA=ppa:me-davidsansome/clementine-dev
REPO=https://clementine-player.googlecode.com/svn/trunk

BASE=`pwd`
DIRECTORY=clementine

# Cleanup any old stuff
rm -rfv $BASE/$DIRECTORY $BASE/*.diff.gz $BASE/*.tar.gz $BASE/*.dsc $BASE/*_source.changes

# Checkout
svn export -r $BUILDBOT_REVISION $REPO $DIRECTORY

# Generate changelog and maketarball.sh
cd $BASE/$DIRECTORY/bin
cmake .. -DBUILDBOT_REVISION=$BUILDBOT_REVISION -DDEB_DIST=$DIST -DWITH_DEBIAN=ON
rm -rfv $BASE/$DIRECTORY/bin/*

# Create the tarball
cd $BASE/$DIRECTORY/dist
./maketarball.sh
mv -v $BASE/$DIRECTORY/dist/*.orig.tar.gz $BASE/
rm -v $BASE/$DIRECTORY/dist/*.tar.gz

# Build the deb
cd $BASE/$DIRECTORY
dpkg-buildpackage -S -kF6ABD82E

# Upload to ppa
cd $BASE
dput $PPA *_source.changes
