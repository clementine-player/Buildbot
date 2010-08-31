# -*- python -*-
# ex: set syntax=python:

from buildbot.buildslave import BuildSlave
from buildbot.changes.svnpoller import SVNPoller
from buildbot.process import factory
from buildbot.process.properties import WithProperties
from buildbot.scheduler import Scheduler, Dependent
from buildbot.status import html, mail
from buildbot.steps.source import SVN
from buildbot.steps.shell import Compile, ShellCommand, Test
from buildbot.steps.transfer import FileUpload
from buildbot.steps.python_twisted import Trial

import clementine_passwords

DEBVERSION  = "0.4.90"
SVNBASEURL  = "http://clementine-player.googlecode.com/svn/"
TRUNK       = SVNBASEURL + "trunk/"
MINGW_DEPS  = SVNBASEURL + "mingw-deps/"
UPLOADBASE  = "/var/www/clementine-player.org/builds"
WORKDIR     = "build/bin"
CMAKE_ENV   = {'BUILDBOT_REVISION': WithProperties("%(revision)s")}
SVN_ARGS    = {"svnurl": TRUNK, "extra_args": ['--accept', 'theirs-full']}
ZAPHOD_JOBS = "-j4"

def split_file(path):
  pieces = path.split('/')
  if pieces[0] == 'branches':
    return ('/'.join(pieces[0:2]),
            '/'.join(pieces[2:]))
  if pieces[0] == 'trunk':
    return (None, '/'.join(pieces[1:]))
  return (pieces[0], '/'.join(pieces[1:]))


# Basic config
c = BuildmasterConfig = {
  'projectName':  "Clementine",
  'projectURL':   "http://www.clementine-player.org/",
  'buildbotURL':  "http://buildbot.clementine-player.org/",
  'slavePortnum': clementine_passwords.PORT,
  'slaves': [
    BuildSlave("zaphod",    clementine_passwords.ZAPHOD, max_builds=2),
    BuildSlave("Chopstick", clementine_passwords.CHOPSTICK),
  ],
  'sources': [
    SVNPoller(
      svnurl=SVNBASEURL,
      pollinterval=60*60, # seconds
      histmax=10,
      svnbin='/usr/bin/svn',
      split_file=split_file,
    ),
  ],
  'status': [
    html.WebStatus(
      http_port="tcp:8010:interface=127.0.0.1",
      allowForce=True,
    ),
    mail.MailNotifier(
      fromaddr="buildmaster@zaphod.purplehatstands.com",
      lookup="gmail.com",
      mode="failing",
    ),
  ],
}


# Schedulers
sched_linux = Scheduler(name="linux", branch=None, treeStableTimer=2*60, builderNames=[
  "Linux Debug",
  "Linux Release",
])

sched_winmac = Scheduler(name="winmac", branch=None, treeStableTimer=2*60, builderNames=[
  "MinGW Debug",
  "MinGW Release",
  "Mac Release",
])

sched_deb = Dependent(name="deb", upstream=sched_linux, builderNames=[
  "Deb Lucid 64-bit",
  "Deb Lucid 32-bit",
])

sched_ppa = Dependent(name="ppa", upstream=sched_deb, builderNames=[
  "PPA Lucid",
])

sched_mingw = Scheduler(name="mingw", branch="mingw-deps", treeStableTimer=2*60, builderNames=[
  "MinGW deps"
])

c['schedulers'] = [
  sched_linux,
  sched_winmac,
  sched_deb,
  sched_ppa,
  sched_mingw,
]


# Builders
def MakeLinuxBuilder(type):
  f = factory.BuildFactory()
  f.addStep(SVN(**SVN_ARGS))
  f.addStep(ShellCommand(workdir=WORKDIR, command=[
      "cmake", "..",
      "-DQT_LCONVERT_EXECUTABLE=/home/buildbot/qtsdk-2010.02/qt/bin/lconvert",
      "-DCMAKE_BUILD_TYPE=" + type,
  ]))
  f.addStep(Compile(workdir=WORKDIR, command=["make", ZAPHOD_JOBS]))
  f.addStep(Test(workdir=WORKDIR, command=[
      "xvfb-run",
      "-a",
      "-n", "10",
      "make", "test"
  ]))
  return f

def MakeDebBuilder(arch, chroot=None):
  schroot_cmd = []
  if chroot is not None:
    schroot_cmd = ["schroot", "-p", "-c", chroot, "--"]

  cmake_cmd = schroot_cmd + ["cmake", ".."]
  dpkg_cmd  = schroot_cmd + ["dpkg-buildpackage", "-b", "-uc", "-us"]

  deb_filename = "clementine_" + DEBVERSION + "~r%(got_revision)s_" + arch + ".deb"

  f = factory.BuildFactory()
  f.addStep(SVN(**SVN_ARGS))
  f.addStep(ShellCommand(command=cmake_cmd, workdir=WORKDIR))
  f.addStep(ShellCommand(command=dpkg_cmd, env=CMAKE_ENV))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc=WithProperties("../" + deb_filename),
      masterdest=WithProperties(UPLOADBASE + "/ubuntu-lucid/" + deb_filename)))
  return f

def MakeMingwBuilder(type, suffix, strip):
  schroot_cmd = ["schroot", "-p", "-c", "mingw", "--"]

  test_env = dict(CMAKE_ENV)
  test_env.update({'GTEST_FILTER': '-Formats/FileformatsTest.GstCanDecode/5:Formats/FileformatsTest.GstCanDecode/6'})

  build_env = dict(CMAKE_ENV)
  build_env.update({'PKG_CONFIG_LIBDIR': '/target/lib/pkgconfig'})

  f = factory.BuildFactory()
  f.addStep(SVN(**SVN_ARGS))
  f.addStep(ShellCommand(workdir=WORKDIR, env=build_env, command=schroot_cmd + [
      "cmake", "..",
      "-DCMAKE_TOOLCHAIN_FILE=/src/Toolchain-mingw32.cmake",
      "-DCMAKE_BUILD_TYPE=" + type,
      "-DQT_HEADERS_DIR=/target/include",
      "-DQT_LIBRARY_DIR=/target/bin",
  ]))
  f.addStep(Compile(command=schroot_cmd + ["make", ZAPHOD_JOBS], workdir=WORKDIR, env=CMAKE_ENV))
  f.addStep(Test(workdir=WORKDIR, env=test_env, command=schroot_cmd + [
      "xvfb-run",
      "-a",
      "-n", "30",
      "make", "test"
  ]))
  f.addStep(ShellCommand(command=schroot_cmd + ["makensis", "clementine.nsi"], workdir="build/dist/windows"))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc="dist/windows/ClementineSetup.exe",
      masterdest=WithProperties(UPLOADBASE + "/win32/ClementineSetup-r%(got_revision)s-" + suffix + ".exe")))
  return f

def MakeMacBuilder():
  f = factory.BuildFactory()
  f.addStep(SVN(**SVN_ARGS))
  f.addStep(ShellCommand(
      workdir=WORKDIR,
      env={'PKG_CONFIG_PATH': '/usr/local/lib/pkgconfig'},
      command=[
        "cmake", "..",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_OSX_ARCHITECTURES=i386",
        "-DQT_QMAKE_EXECUTABLE=/usr/local/Trolltech/Qt-4.7.0/bin/qmake",
        "-DCMAKE_OSX_SYSROOT=/Developer/SDKs/MacOSX10.6.sdk",
        "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.6",
      ],
  ))
  f.addStep(Compile(command=["make", "-j2"], workdir=WORKDIR))
  f.addStep(Test(
      command=["make", "test", "-j2"],
      workdir=WORKDIR,
      env={'DYLD_FRAMEWORK_PATH': '/usr/local/Trolltech/Qt-4.7.0/lib',
          'GTEST_FILTER': '-Formats/FileformatsTest.GstCanDecode*:SongLoaderTest.LoadRemote*'}))
  f.addStep(ShellCommand(command=["make", "install"], workdir=WORKDIR))
  f.addStep(ShellCommand(command=["make", "bundle"], workdir=WORKDIR))
  f.addStep(ShellCommand(command=["make", "dmg"], workdir=WORKDIR))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc="bin/clementine.dmg",
      masterdest=WithProperties(UPLOADBASE + "/mac/clementine-r%(got_revision)s-rel.dmg")))
  return f

def MakePPABuilder():
  f = factory.BuildFactory()
  f.addStep(ShellCommand(command=["/home/buildbot/uploadtoppa.sh"],
    env=CMAKE_ENV,
    workdir="build",
  ))
  return f

def MakeMinGWDepsBuilder():
  schroot_cmd = ["schroot", "-p", "-c", "mingw", "-d", "/src", "--"]

  f = factory.BuildFactory()
  f.addStep(ShellCommand(command=schroot_cmd + ["svn", "up"]))
  f.addStep(ShellCommand(command=schroot_cmd + ["make", "clean"]))
  f.addStep(ShellCommand(command=schroot_cmd + ["make"]))
  return f

def BuilderDef(name, dir, factory, slave="zaphod"):
  return {
    'name': name,
    'builddir': dir,
    'factory': factory,
    'slavename': slave,
  }

c['builders'] = [
  BuilderDef("Linux Debug",      "clementine_linux_debug",   MakeLinuxBuilder('Debug')),
  BuilderDef("Linux Release",    "clementine_linux_release", MakeLinuxBuilder('Release')),
  BuilderDef("Deb Lucid 64-bit", "clementine_deb_lucid_64",  MakeDebBuilder('amd64')),
  BuilderDef("Deb Lucid 32-bit", "clementine_deb_lucid_32",  MakeDebBuilder('i386', chroot='lucid-32')),
  BuilderDef("PPA Lucid",        "clementine_ppa",           MakePPABuilder()),
  BuilderDef("MinGW Debug",      "clementine_mingw_debug",   MakeMingwBuilder('Debug', 'dbg', strip=False)),
  BuilderDef("MinGW Release",    "clementine_mingw_release", MakeMingwBuilder('Release', 'rel', strip=True)),
  BuilderDef("Mac Release",      "clementine_mac_release",   MakeMacBuilder(), slave="Chopstick"),
  BuilderDef("MinGW deps",       "clementine_mingw_deps",    MakeMinGWDepsBuilder()),
]

