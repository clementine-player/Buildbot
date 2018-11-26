import json
import os

from twisted.application import service

slavename = open('/slave-name').read().strip()
basedir = os.path.join('/persistent-data', slavename)
PASSWORDS = json.load(open('/config/passwords.json'))

buildmaster_host = os.environ['MASTER_PORT_9989_TCP_ADDR']
port = int(os.environ['MASTER_PORT_9989_TCP_PORT'])
passwd = PASSWORDS[slavename]
keepalive = 600
usepty = 0
umask = None
maxdelay = 300
allow_shutdown = None

try:
  from buildslave.bot import BuildSlave as Worker
  application = service.Application('buildslave')
  s = Worker(buildmaster_host, port, slavename, passwd, basedir,
             keepalive, usepty, umask=umask, maxdelay=maxdelay,
             allow_shutdown=allow_shutdown)
except:
  from buildbot_worker.bot import Worker
  application = service.Application('buildbot-worker')
  s = Worker(buildmaster_host, port, slavename, passwd, basedir,
             keepalive, umask=umask, maxdelay=maxdelay,
             allow_shutdown=allow_shutdown)

s.setServiceParent(application)
