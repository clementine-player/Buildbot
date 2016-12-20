from clementine/slave-ubuntu-trusty-64

# Secure version of urllib3 compiles some stuff from source.
run apt-get update
run apt-get install -y libffi-dev libssl-dev

# transifex client
run pip install transifex-client
run pip install --upgrade urllib3[secure]  # build-in package doesn't have "six"

# .ssh directory for pushing to github.
# The mkdir and chown are in the same line because of
# https://github.com/docker/docker/issues/6047
run mkdir --mode=0700 /home/buildbot/.ssh && chown buildbot:buildbot /home/buildbot/.ssh
add known_hosts /home/buildbot/.ssh/

# Give the buildslave a name
run echo "transifex" > /slave-name
