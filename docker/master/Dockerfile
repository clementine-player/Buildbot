from ubuntu

run apt-get update && apt-get install -y python-pip python-dev git
run pip install sqlalchemy==0.7.10 buildbot

expose 9989
env PYTHONPATH /config/master
entrypoint ["/usr/bin/python", "/config/master/start.py"]
cmd []
