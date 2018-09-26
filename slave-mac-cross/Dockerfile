FROM clementine/mac:1.3

RUN apt-get update && apt-get install -y python-pip python-dev
RUN pip install buildbot_slave

RUN rm -rf /root && mkdir /root --mode 0755
RUN echo "mac-cross" > /slave-name

# Create the buildbot user.
run useradd -r -m -s /bin/false buildbot
cmd ["/usr/bin/python", "/config/slave/start.py"]
