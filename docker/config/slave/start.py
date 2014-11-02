import os

slavename = open('/slave-name').read().strip()
basedir = os.path.join('/persistent-data', slavename)

# Create the basedir if it doesn't exist.
if not os.path.exists(basedir):
  os.mkdir(basedir)
  os.symlink('/config/slave/buildbot.tac', os.path.join(basedir, 'buildbot.tac'))
  os.symlink('/config/slave/info', os.path.join(basedir, 'info'))

os.execl(
    '/usr/local/bin/buildslave',
    'buildslave', 'start', '--nodaemon', basedir)
