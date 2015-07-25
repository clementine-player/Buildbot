import os
import pwd
import shutil
import subprocess

SLAVENAME = open('/slave-name').read().strip()
BASEDIR = os.path.join('/persistent-data', SLAVENAME)

pwd_entry = pwd.getpwnam('buildbot')
creating_basedir = True

# Create the BASEDIR if it doesn't exist.
if not os.path.exists(BASEDIR):
  os.mkdir(BASEDIR)
  os.chown(BASEDIR, pwd_entry.pw_uid, pwd_entry.pw_gid)
  creating_basedir = True

  if os.path.exists('/first-time-setup.sh'):
    try:
      stdout = subprocess.check_output(
          ['/bin/sh', '/first-time-setup.sh'],
          stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
      shutil.rmtree(BASEDIR)
      raise

    with open(os.path.join(BASEDIR, 'first-time-setup.log'), 'w') as fh:
      fh.write(stdout)

# Change to the buildbot user.
os.setgid(pwd_entry.pw_gid)
os.setuid(pwd_entry.pw_uid)

if creating_basedir:
  os.symlink('/config/slave/buildbot.tac', os.path.join(BASEDIR, 'buildbot.tac'))
  os.symlink('/config/slave/info', os.path.join(BASEDIR, 'info'))

pidfile = os.path.join(BASEDIR, 'twistd.pid')
if os.path.exists(pidfile):
  os.unlink(pidfile)

os.execlp(
    'buildslave',
    'buildslave', 'start', '--nodaemon', BASEDIR)
