from clementine/slave-ubuntu-trusty-32

# libspotify.
add https://developer.spotify.com/download/libspotify/libspotify-12.1.51-Linux-i686-release.tar.gz /src/
run cd /src && tar -xf libspotify-12.1.51-Linux-i686-release.tar.gz
run cd /src/libspotify-12.1.51-Linux-i686-release && make install

# Give the buildslave a name
run echo "spotify-blob-32" > /slave-name
