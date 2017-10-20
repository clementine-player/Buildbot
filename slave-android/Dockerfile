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
run cd /tmp && wget https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip
run mkdir /android-sdk-linux && chmod 755 /android-sdk-linux
run unzip -d /android-sdk-linux /tmp/sdk-tools-linux-3859397.zip

run yes | /android-sdk-linux/tools/bin/sdkmanager --licenses
run yes | /android-sdk-linux/tools/bin/sdkmanager --update
run yes | /android-sdk-linux/tools/bin/sdkmanager "platforms;android-25" "build-tools;25.0.3" "extras;google;m2repository" "extras;android;m2repository"
run yes | /android-sdk-linux/tools/bin/sdkmanager --licenses

# Give the buildslave a name
run echo "android" > /slave-name

# Create the buildbot user.
run useradd -r -m -s /bin/false buildbot
cmd ["/usr/bin/python", "/config/slave/start.py"]
