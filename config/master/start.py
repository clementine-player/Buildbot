import argparse
import os
import pwd
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
parser.add_argument('--reconfig', action='store_true')
args = parser.parse_args()

BASEDIR = '/persistent-data/master'

pwd_entry = pwd.getpwnam('buildbot')
creating_basedir = False

# Create the BASEDIR if it doesn't exist.
if not os.path.exists(BASEDIR):
  os.mkdir(BASEDIR)
  os.chown(BASEDIR, pwd_entry.pw_uid, pwd_entry.pw_gid)
  creating_basedir = True

# Change to the buildbot user.
os.setgid(pwd_entry.pw_gid)
os.setuid(pwd_entry.pw_uid)

if creating_basedir:
  subprocess.check_call(['buildbot', 'create-master', BASEDIR])
  os.symlink('/config/master/master.cfg.py', os.path.join(BASEDIR, 'master.cfg'))

if not args.reconfig:
  pidfile = os.path.join(BASEDIR, 'twistd.pid')
  if os.path.exists(pidfile):
    os.unlink(pidfile)

if args.debug:
  argv = ['buildbot', 'start', BASEDIR]
elif args.reconfig:
  argv = ['buildbot', 'reconfig', BASEDIR]
else:
  argv = ['buildbot', 'start', '--nodaemon', BASEDIR]

os.execv('/usr/local/bin/buildbot', argv)
