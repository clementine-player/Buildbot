from ubuntu

run apt-get update && apt-get install -y python-pip python-dev git
run pip install buildbot==1.6.0

run useradd -r -s /bin/false buildbot

expose 9989
env PYTHONPATH /config/master
entrypoint ["/usr/bin/python", "/config/master/start.py"]
cmd []
