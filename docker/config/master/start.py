import argparse
import os
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
parser.add_argument('--reconfig', action='store_true')
args = parser.parse_args()

basedir = os.path.join('/persistent-data/master')

# Create the basedir if it doesn't exist.
if not os.path.exists(basedir):
  os.mkdir(basedir)
  subprocess.check_call(['buildbot', 'create-master', basedir])
  os.symlink('/config/master/master.cfg.py', os.path.join(basedir, 'master.cfg'))

if not args.reconfig:
  pidfile = os.path.join(basedir, 'twistd.pid')
  if os.path.exists(pidfile):
    os.unlink(pidfile)

if args.debug:
  argv = ['buildbot', 'start', basedir]
elif args.reconfig:
  argv = ['buildbot', 'reconfig', basedir]
else:
  argv = ['buildbot', 'start', '--nodaemon', basedir]

os.execv('/usr/local/bin/buildbot', argv)
