from thyrlian/android-sdk

run apt-get update && apt-get install -y \
    # Buildbot slave
    python-pip python-dev git

run pip install buildbot_slave

run chgrp -R buildbot /opt/android-sdk
run chmod -R g+w /opt/android-sdk

# Give the buildslave a name
run echo "android" > /slave-name

# Create the buildbot user.
run useradd -r -m -s /bin/false buildbot
cmd ["/usr/bin/python", "/config/slave/start.py"]
