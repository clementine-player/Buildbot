from ubuntu:trusty

run apt-get update && apt-get install -y \
    # Buildbot slave
    python-pip python-dev git \
    # Android SDK dependencies.
    openjdk-7-jdk unzip wget libc6-i386 lib32stdc++6 lib32z1

run pip install buildbot_slave

# Android SDK.
run cd /tmp && wget http://dl.google.com/android/android-sdk_r24.3.4-linux.tgz
run cd / && tar -xvf /tmp/android-sdk_r24.3.4-linux.tgz
run echo y | /android-sdk-linux/tools/android update sdk --no-ui --all \
  --filter android-22,build-tools-22.0.1,extra-android-support,extra-android-m2repository

# Give the buildslave a name
run echo "android" > /slave-name

# Create the buildbot user.
run useradd -r -m -s /bin/false buildbot
cmd ["/usr/bin/python", "/config/slave/start.py"]
