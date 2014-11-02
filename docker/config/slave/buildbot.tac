import os

from buildslave.bot import BuildSlave
from twisted.application import service

application = service.Application('buildslave')

slavename = open('/slave-name').read().strip()
basedir = os.path.join('/persistent-data', slavename)

buildmaster_host = os.environ['MASTER_PORT_9989_TCP_ADDR']
port = int(os.environ['MASTER_PORT_9989_TCP_PORT'])
passwd = 'hunter2'
keepalive = 600
usepty = 0
umask = None
maxdelay = 300
allow_shutdown = None

s = BuildSlave(buildmaster_host, port, slavename, passwd, basedir,
               keepalive, usepty, umask=umask, maxdelay=maxdelay,
               allow_shutdown=allow_shutdown)
s.setServiceParent(application)