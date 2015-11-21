from clementine/slave-ubuntu-trusty-64

# libspotify.
add https://developer.spotify.com/download/libspotify/libspotify-12.1.51-Linux-x86_64-release.tar.gz /src/
run cd /src && tar -xf libspotify-12.1.51-Linux-x86_64-release.tar.gz
run cd /src/libspotify-12.1.51-Linux-x86_64-release && make install

# Give the buildslave a name
run echo "spotify-blob-64" > /slave-name
