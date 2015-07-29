#/bin/sh -e

mkdir -v -p /persistent-data/mingw/target/bin \
            /persistent-data/mingw/target/stow \
            /persistent-data/mingw/windows-dependencies/source
chown -v -R buildbot:buildbot /persistent-data/mingw/target \
                              /persistent-data/mingw/windows-dependencies/source

ln -v -s /mingw/i686-w64-mingw32/lib/libgcc_s_sjlj-1.dll /target/bin/
