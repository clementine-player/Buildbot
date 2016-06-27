from ubuntu:xenial

run apt-get update && apt-get install -y \
    # Buildbot slave
    python-pip python-dev git \
    # Android SDK dependencies.
    openjdk-8-jdk unzip wget libc6-i386 lib32stdc++6 lib32z1 \
    # For accepting licenses.
    expect

run pip install buildbot_slave

# Android SDK.
run cd /tmp && wget https://dl.google.com/android/android-sdk_r24.4.1-linux.tgz
run cd / && tar -xvf /tmp/android-sdk_r24.4.1-linux.tgz

add install-sdk.exp /install-sdk.exp
run expect /install-sdk.exp

# Give the buildslave a name
run echo "android" > /slave-name

# Create the buildbot user.
run useradd -r -m -s /bin/false buildbot
cmd ["/usr/bin/python", "/config/slave/start.py"]
