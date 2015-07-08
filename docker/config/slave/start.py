import os
import shutil
import subprocess

slavename = open('/slave-name').read().strip()
basedir = os.path.join('/persistent-data', slavename)

# Create the basedir if it doesn't exist.
if not os.path.exists(basedir):
  os.mkdir(basedir)
  os.symlink('/config/slave/buildbot.tac', os.path.join(basedir, 'buildbot.tac'))
  os.symlink('/config/slave/info', os.path.join(basedir, 'info'))

  if os.path.exists('/first-time-setup.sh'):
    try:
      stdout = subprocess.check_output(
          ['/bin/sh', '/first-time-setup.sh'],
          stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
      shutil.rmtree(basedir)
      raise

    with open(os.path.join(basedir, 'first-time-setup.log'), 'w') as fh:
      fh.write(stdout)

pidfile = os.path.join(basedir, 'twistd.pid')
if os.path.exists(pidfile):
  os.unlink(pidfile)

os.execlp(
    'buildslave',
    'buildslave', 'start', '--nodaemon', basedir)
