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
from buildbot.steps.transfer import FileUpload, DirectoryUpload
from buildbot.steps.python_twisted import Trial

import clementine_passwords

DEBVERSION  = "0.6.90"
SVNBASEURL  = "http://svn.clementine-player.org/clementine-mirror/"
MINGW_DEPS  = SVNBASEURL + "mingw-deps/"
UPLOADBASE  = "/var/www/clementine-player.org/builds"
UPLOADDOCS  = "/var/www/clementine-player.org/docs/unstable"
WORKDIR     = "build/bin"
SVN_ARGS    = {"baseURL": SVNBASEURL, "defaultBranch": "trunk/", "always_purge": True, "mode": "clobber"}
ZAPHOD_JOBS = "-j4"

DISABLED_TESTS = [
  'Formats/FileformatsTest.*',
  'SongLoaderTest.*'
]
TEST_ENV = {'GTEST_FILTER': '-' + ':'.join(DISABLED_TESTS) }

def split_file(path):
  pieces = path.split('/')
  if pieces[0] == 'branches':
    return ('/'.join(pieces[0:2]),
            '/'.join(pieces[2:]))
  if pieces[0] == 'trunk':
    return (None, '/'.join(pieces[1:]))
  return (pieces[0], '/'.join(pieces[1:]))

class OutputFinder(ShellCommand):
  def __init__(self, pattern=None, **kwargs):
    if pattern is None:
      ShellCommand.__init__(self, **kwargs)
    else:
      ShellCommand.__init__(self,
        name="get output filename",
        command=["sh", "-c", "basename `ls " + pattern + "|head -n 1`"],
        **kwargs
      )

  def commandComplete(self, cmd):
    filename = self.getLog('stdio').readlines()[0].strip()
    self.setProperty("output-filename", filename)

# Basic config
c = BuildmasterConfig = {
  'projectName':  "Clementine",
  'projectURL':   "http://www.clementine-player.org/",
  'buildbotURL':  "http://buildbot.clementine-player.org/",
  'slavePortnum': clementine_passwords.PORT,
  'slaves': [
    BuildSlave("zaphod",    clementine_passwords.ZAPHOD, max_builds=2, notify_on_missing="me@davidsansome.com"),
    BuildSlave("zarquon",   clementine_passwords.ZARQUON, notify_on_missing="me@davidsansome.com"),
    BuildSlave("grunthos",  clementine_passwords.GRUNTHOS, max_builds=1, notify_on_missing="me@davidsansome.com"),
  ],
  'sources': [
    SVNPoller(
      svnurl=SVNBASEURL,
      pollinterval=60*5, # seconds
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
  "Linux Clang",
])

sched_winmac = Scheduler(name="winmac", branch=None, treeStableTimer=2*60, builderNames=[
  "MinGW Debug",
  "MinGW Release",
  "Mac Release",
])

sched_deb = Dependent(name="deb", upstream=sched_linux, builderNames=[
  "Deb Lucid 64-bit",
  "Deb Lucid 32-bit",
  "Deb Maverick 64-bit",
  "Deb Maverick 32-bit",
  "Deb Squeeze 64-bit",
  "Deb Squeeze 32-bit",
])

sched_rpm = Dependent(name="rpm", upstream=sched_linux, builderNames=[
  "Rpm Fedora 13 64-bit",
  "Rpm Fedora 13 32-bit",
  "Rpm Fedora 14 64-bit",
  "Rpm Fedora 14 32-bit",
])

sched_ppa = Dependent(name="ppa", upstream=sched_deb, builderNames=[
  "PPA Lucid",
  "PPA Maverick",
  "PPA Natty",
])

sched_mingw = Scheduler(name="mingw", branch="mingw-deps", treeStableTimer=2*60, builderNames=[
  "MinGW deps"
])

sched_doc = Dependent(name="doc", upstream=sched_linux, builderNames=[
  "Python docs",
])

c['schedulers'] = [
  sched_linux,
  sched_winmac,
  sched_deb,
  sched_rpm,
  sched_ppa,
  sched_mingw,
  sched_doc,
]


# Builders
def MakeLinuxBuilder(type, clang=False):
  cmake_args = [
    "cmake", "..",
    "-DQT_LCONVERT_EXECUTABLE=/home/buildbot/qtsdk-2010.02/qt/bin/lconvert",
    "-DCMAKE_BUILD_TYPE=" + type,
  ]

  if clang:
    cmake_args.append("-DCMAKE_C_COMPILER=clang")
    cmake_args.append("-DCMAKE_CXX_COMPILER=clang++")

  f = factory.BuildFactory()
  f.addStep(SVN(**SVN_ARGS))
  f.addStep(ShellCommand(name="cmake", workdir=WORKDIR, haltOnFailure=True, command=cmake_args))
  f.addStep(Compile(workdir=WORKDIR, haltOnFailure=True, command=["make", ZAPHOD_JOBS]))
  f.addStep(Test(workdir=WORKDIR, env=TEST_ENV, command=[
      "xvfb-run",
      "-a",
      "-n", "10",
      "make", "test"
  ]))
  return f

def MakeDocBuilder():
  cmake_args = [
    "cmake", "..",
    "-DQT_LCONVERT_EXECUTABLE=/home/buildbot/qtsdk-2010.02/qt/bin/lconvert",
  ]

  f = factory.BuildFactory()
  f.addStep(SVN(**SVN_ARGS))
  f.addStep(ShellCommand(name="cmake", workdir=WORKDIR, haltOnFailure=True, command=cmake_args))
  f.addStep(Compile(workdir=WORKDIR, haltOnFailure=True, command=[
    "xvfb-run",
    "-a", "-n", "20",
    "make", "pythondocs", ZAPHOD_JOBS,
  ]))
  f.addStep(DirectoryUpload(
    slavesrc="bin/doc/python/output",
    masterdest=UPLOADDOCS,
  ))
  return f

def MakeDebBuilder(arch, dist, chroot=None, dist_type="ubuntu"):
  schroot_cmd = []
  if chroot is not None:
    schroot_cmd = ["schroot", "-p", "-c", chroot, "--"]

  cmake_cmd = schroot_cmd + ["cmake", "..", "-DWITH_DEBIAN=ON", "-DDEB_ARCH=" + arch, "-DDEB_DIST=" + dist]
  make_cmd  = schroot_cmd + ["make", "deb", ZAPHOD_JOBS]

  f = factory.BuildFactory()
  f.addStep(SVN(**SVN_ARGS))
  f.addStep(ShellCommand(name="cmake", command=cmake_cmd, haltOnFailure=True, workdir=WORKDIR))
  f.addStep(Compile(command=make_cmd, haltOnFailure=True, workdir=WORKDIR))
  f.addStep(OutputFinder(pattern="bin/clementine_*.deb"))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc=WithProperties("bin/%(output-filename)s"),
      masterdest=WithProperties(UPLOADBASE + "/" + dist_type + "-" + dist + "/%(output-filename)s")))
  return f

def MakeRpmBuilder(distro, arch, chroot, upload_ver):
  f = factory.BuildFactory()
  f.addStep(SVN(**SVN_ARGS))
  f.addStep(ShellCommand(name="cmake", workdir=WORKDIR, haltOnFailure=True, command=[
      "cmake", "..",
      "-DRPM_DISTRO=" + distro,
      "-DRPM_ARCH=" + arch,
      "-DMOCK_CHROOT=" + chroot,
  ]))
  f.addStep(Compile(command=["make", ZAPHOD_JOBS, "rpm"], workdir=WORKDIR, haltOnFailure=True))
  f.addStep(OutputFinder(pattern="bin/clementine-*.rpm"))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc=WithProperties("bin/%(output-filename)s"),
      masterdest=WithProperties(UPLOADBASE + "/fedora-" + upload_ver + "/%(output-filename)s")))
  return f

def MakeMingwBuilder(type, suffix, strip):
  schroot_cmd = ["schroot", "-p", "-c", "mingw", "--"]

  test_env = dict(TEST_ENV)

  build_env = {'PKG_CONFIG_LIBDIR': '/target/lib/pkgconfig'}

  f = factory.BuildFactory()
  f.addStep(SVN(**SVN_ARGS))
  f.addStep(ShellCommand(name="cmake", workdir=WORKDIR, env=build_env, haltOnFailure=True, command=schroot_cmd + [
      "cmake", "..",
      "-DCMAKE_TOOLCHAIN_FILE=/src/Toolchain-mingw32.cmake",
      "-DCMAKE_BUILD_TYPE=" + type,
      "-DQT_HEADERS_DIR=/target/include",
      "-DQT_LIBRARY_DIR=/target/bin",
  ]))
  f.addStep(ShellCommand(name="link dependencies", workdir=WORKDIR, haltOnFailure=True, command=schroot_cmd + [
      "sh", "-c",
      "ln -svf /src/clementine-deps/* ../dist/windows/",
  ]))
  f.addStep(ShellCommand(name="link output", workdir="build/dist/windows", haltOnFailure=True, command=schroot_cmd + [
      "ln", "-svf", "../../bin/clementine.exe", ".",
  ]))
  f.addStep(ShellCommand(name="test", workdir=WORKDIR, haltOnFailure=True, command=schroot_cmd + [
      "sh", "-c",
      "ln -svf /src/clementine-deps/* tests/",
  ]))
  f.addStep(Compile(command=schroot_cmd + ["make", ZAPHOD_JOBS], workdir=WORKDIR, haltOnFailure=True))
  f.addStep(Test(workdir=WORKDIR, env=test_env, command=schroot_cmd + [
      "xvfb-run",
      "-a",
      "-n", "30",
      "make", "test"
  ]))
  f.addStep(ShellCommand(name="makensis", command=schroot_cmd + ["makensis", "clementine.nsi"], workdir="build/dist/windows", haltOnFailure=True))
  f.addStep(OutputFinder(pattern="dist/windows/ClementineSetup*.exe"))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc=WithProperties("dist/windows/%(output-filename)s"),
      masterdest=WithProperties(UPLOADBASE + "/win32/" + suffix + "/%(output-filename)s")))
  return f

def MakeMacBuilder():
  test_env = dict(TEST_ENV)
  test_env.update({
    'DYLD_FRAMEWORK_PATH': '/usr/local/Trolltech/Qt-4.7.0/lib',
    'GTEST_FILTER': '-Formats/FileformatsTest.GstCanDecode*:SongLoaderTest.LoadRemote*',
  })

  f = factory.BuildFactory()
  f.addStep(SVN(**SVN_ARGS))
  f.addStep(ShellCommand(
      name="cmake",
      workdir=WORKDIR,
      env={'PKG_CONFIG_PATH': '/usr/local/lib/pkgconfig'},
      command=[
        "cmake", "..",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_OSX_ARCHITECTURES=i386",
        "-DCMAKE_OSX_SYSROOT=/Developer/SDKs/MacOSX10.6.sdk",
        "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.6",
      ],
      haltOnFailure=True,
  ))
  f.addStep(Compile(command=["make"], workdir=WORKDIR, haltOnFailure=True))
#  f.addStep(Test(
#      command=["make", "test"],
#      workdir=WORKDIR,
#      env=TEST_ENV))
  f.addStep(ShellCommand(name="install", command=["make", "install"], haltOnFailure=True, workdir=WORKDIR))
  f.addStep(ShellCommand(name="dmg", command=["make", "dmg"], haltOnFailure=True, workdir=WORKDIR))
  f.addStep(OutputFinder(pattern="bin/clementine-*.dmg"))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc=WithProperties("bin/%(output-filename)s"),
      masterdest=WithProperties(UPLOADBASE + "/mac/%(output-filename)s")))
  return f

def MakePPABuilder(dist, chroot=None):
  schroot_cmd = []
  if chroot is not None:
    schroot_cmd = ["schroot", "-p", "-c", chroot, "--"]

  ppa_env = {'DIST': dist}

  f = factory.BuildFactory()
  f.addStep(ShellCommand(command=schroot_cmd + ["/home/buildbot/uploadtoppa.sh"],
    name="upload",
    env=ppa_env,
    workdir="build",
  ))
  return f

def MakeMinGWDepsBuilder():
  schroot_cmd = ["schroot", "-p", "-c", "mingw", "-d", "/src", "--"]

  f = factory.BuildFactory()
  f.addStep(ShellCommand(name="checkout", command=schroot_cmd + ["svn", "up"]))
  f.addStep(ShellCommand(name="clean", command=schroot_cmd + ["make", "clean"]))
  f.addStep(ShellCommand(name="compile", command=schroot_cmd + ["make"]))
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
  BuilderDef("Linux Clang",      "clementine_linux_clang",   MakeLinuxBuilder('Release', clang=True)),
  BuilderDef("Deb Lucid 64-bit", "clementine_deb_lucid_64",  MakeDebBuilder('amd64', 'lucid')),
  BuilderDef("Deb Lucid 32-bit", "clementine_deb_lucid_32",  MakeDebBuilder('i386',  'lucid', chroot='lucid-32')),
  BuilderDef("Deb Maverick 64-bit", "clementine_deb_maverick_64", MakeDebBuilder('amd64', 'maverick', chroot='maverick-64')),
  BuilderDef("Deb Maverick 32-bit", "clementine_deb_maverick_32", MakeDebBuilder('i386',  'maverick', chroot='maverick-32')),
  BuilderDef("Deb Squeeze 64-bit", "clementine_deb_squeeze_64", MakeDebBuilder('amd64', 'squeeze', chroot='squeeze-64', dist_type='debian')),
  BuilderDef("Deb Squeeze 32-bit", "clementine_deb_squeeze_32", MakeDebBuilder('i386',  'squeeze', chroot='squeeze-32', dist_type='debian')),
  BuilderDef("Rpm Fedora 13 64-bit", "clementine_rpm_fc13_64", MakeRpmBuilder('fc13', 'x86_64', 'fedora-13-x86_64', '13'), slave="grunthos"),
  BuilderDef("Rpm Fedora 13 32-bit", "clementine_rpm_fc13_32", MakeRpmBuilder('fc13', 'i686',   'fedora-13-i386',   '13'), slave="grunthos"),
  BuilderDef("Rpm Fedora 14 64-bit", "clementine_rpm_fc14_64", MakeRpmBuilder('fc14', 'x86_64', 'fedora-14-x86_64', '14'), slave="grunthos"),
  BuilderDef("Rpm Fedora 14 32-bit", "clementine_rpm_fc14_32", MakeRpmBuilder('fc14', 'i686',   'fedora-14-i386',   '14'), slave="grunthos"),
  BuilderDef("PPA Lucid",        "clementine_ppa",           MakePPABuilder('lucid')),
  BuilderDef("PPA Maverick",     "clementine_ppa_maverick",  MakePPABuilder('maverick', chroot='maverick-64')),
  BuilderDef("PPA Natty",        "clementine_ppa_natty",     MakePPABuilder('natty', chroot='natty-32')),
  BuilderDef("MinGW Debug",      "clementine_mingw_debug",   MakeMingwBuilder('Debug', 'debug', strip=False)),
  BuilderDef("MinGW Release",    "clementine_mingw_release", MakeMingwBuilder('Release', 'release', strip=True)),
  BuilderDef("Mac Release",      "clementine_mac_release",   MakeMacBuilder(), slave="zarquon"),
  BuilderDef("MinGW deps",       "clementine_mingw_deps",    MakeMinGWDepsBuilder()),
  BuilderDef("Python docs",      "clementine_pythondocs",    MakeDocBuilder()),
]

