# -*- python -*-
# ex: set syntax=python:

from buildbot.buildslave import BuildSlave
from buildbot.changes.gitpoller import GitPoller
from buildbot.process import factory
from buildbot.process.properties import WithProperties
from buildbot.scheduler import Scheduler, Dependent
from buildbot.schedulers.filter import ChangeFilter
from buildbot.status import html, mail
from buildbot.steps.master import MasterShellCommand
from buildbot.steps.source import Git
from buildbot.steps.shell import Compile, ShellCommand, Test, SetProperty
from buildbot.steps.transfer import FileUpload, DirectoryUpload
from buildbot.steps.python_twisted import Trial

import clementine_passwords

import os

DEBVERSION  = "0.6.90"
GITBASEURL  = "https://code.google.com/p/clementine-player/"
UPLOADBASE  = "/var/www/clementine-player.org/builds"
UPLOADDOCS  = "/var/www/clementine-player.org/docs/unstable"
SPOTIFYBASE = "/var/www/clementine-player.org/spotify"
WORKDIR     = "build/bin"
GIT_ARGS    = {
  "repourl": GITBASEURL,
  "branch": "master",
  "mode": "clobber",
  "retry": (5*60, 3),
}
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
        command=["sh", "-c", "basename `ls -d " + pattern + "|head -n 1`"],
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
  ],
  'change_source': [
    GitPoller(
      repourl=GITBASEURL,
      pollinterval=60*5, # seconds
      branch='master',
      workdir="gitpoller_work",
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

change_filter = ChangeFilter(project_re=r'.*', branch=u'master')

# Schedulers
sched_linux = Scheduler(name="linux", change_filter=change_filter, treeStableTimer=2*60, builderNames=[
  "Linux Debug",
  "Linux Release",
  "Linux Clang",
  "Linux GCC 4.6.0",
  "Linux Minimal",
])

sched_winmac = Scheduler(name="winmac", change_filter=change_filter, treeStableTimer=2*60, builderNames=[
  "MinGW Debug",
  "MinGW Release",
  "Mac Release",
])

sched_deb = Dependent(name="deb", upstream=sched_linux, builderNames=[
  "Deb Lucid 64-bit",
  "Deb Lucid 32-bit",
  "Deb Maverick 64-bit",
  "Deb Maverick 32-bit",
  "Deb Natty 64-bit",
  "Deb Natty 32-bit",
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

sched_dependencies = Scheduler(name="dependencies", branch="dependencies", treeStableTimer=2*60, builderNames=[
  "Dependencies Mingw",
  "Dependencies Mac",
])

sched_spotifyblob = Dependent(name="spotifyblob", upstream=sched_linux, builderNames=[
  "Spotify blob 32-bit",
  "Spotify blob 64-bit",
])

c['schedulers'] = [
  sched_linux,
  sched_winmac,
  sched_deb,
  sched_rpm,
  sched_ppa,
  sched_dependencies,
  sched_spotifyblob,
]


# Builders
def MakeLinuxBuilder(type, clang=False, gcc460=False, disable_everything=False):
  cmake_args = [
    "cmake", "..",
    "-DQT_LCONVERT_EXECUTABLE=/home/buildbot/qtsdk-2010.02/qt/bin/lconvert",
    "-DCMAKE_BUILD_TYPE=" + type,
  ]
  test_env = dict(TEST_ENV)

  if clang:
    cmake_args.append("-DCMAKE_C_COMPILER=clang")
    cmake_args.append("-DCMAKE_CXX_COMPILER=clang++")

  if gcc460:
    cmake_args.append("-DCMAKE_C_COMPILER=/usr/local/gcc-4.6.0/bin/gcc")
    cmake_args.append("-DCMAKE_CXX_COMPILER=/usr/local/gcc-4.6.0/bin/g++")
    test_env['LD_LIBRARY_PATH'] = '/usr/local/gcc-4.6.0/lib64'

  if disable_everything:
    cmake_args += [
      "-DBUNDLE_PROJECTM_PRESETS=OFF",
      "-DENABLE_DBUS=OFF",
      "-DENABLE_DEVICEKIT=OFF",
      "-DENABLE_GIO=OFF",
      "-DENABLE_IMOBILEDEVICE=OFF",
      "-DENABLE_LIBGPOD=OFF",
      "-DENABLE_LIBLASTFM=OFF",
      "-DENABLE_LIBMTP=OFF",
      "-DENABLE_REMOTE=OFF",
      "-DENABLE_SCRIPTING_ARCHIVES=OFF",
      "-DENABLE_SCRIPTING_PYTHON=OFF",
      "-DENABLE_SOUNDMENU=OFF",
      "-DENABLE_SPARKLE=OFF",
      "-DENABLE_VISUALISATIONS=OFF",
      "-DENABLE_WIIMOTEDEV=OFF",
      "-DUSE_SYSTEM_PROJECTM=OFF",
      "-DUSE_SYSTEM_QTSINGLEAPPLICATION=OFF",
      "-DUSE_SYSTEM_QXT=OFF",
    ]

  f = factory.BuildFactory()
  f.addStep(Git(**GIT_ARGS))
  f.addStep(ShellCommand(name="cmake", workdir=WORKDIR, haltOnFailure=True, command=cmake_args))
  f.addStep(Compile(workdir=WORKDIR, haltOnFailure=True, command=["make", ZAPHOD_JOBS]))
  f.addStep(Test(workdir=WORKDIR, env=test_env, command=[
      "xvfb-run",
      "-a",
      "-n", "10",
      "make", "test"
  ]))
  return f

def MakeSpotifyBlobBuilder(chroot=None):
  schroot_cmd = []
  if chroot is not None:
    schroot_cmd = ["schroot", "-p", "-c", chroot, "--"]

  cmake_args = [
    "cmake", "..",
    "-DQT_LCONVERT_EXECUTABLE=/home/buildbot/qtsdk-2010.02/qt/bin/lconvert",
    "-DPROTOBUF_INCLUDE_DIR=/usr/local/protobuf-2.4.0a/include",
    "-DPROTOBUF_PROTOC_EXECUTABLE=/usr/local/protobuf-2.4.0a/bin/protoc",
    "-DPROTOBUF_LITE_LIBRARY=/usr/local/protobuf-2.4.0a/lib/libprotobuf-lite.a",
    "-DCMAKE_INSTALL_PREFIX=%s/installprefix" % WORKDIR,
  ]

  cmake_cmd = schroot_cmd + cmake_args
  make_cmd  = schroot_cmd + ["make"]

  f = factory.BuildFactory()
  f.addStep(Git(**GIT_ARGS))
  f.addStep(ShellCommand(name="cmake", workdir=WORKDIR, haltOnFailure=True, command=cmake_cmd))
  f.addStep(Compile(workdir=WORKDIR, haltOnFailure=True, command=make_cmd + ["clementine-spotifyblob", ZAPHOD_JOBS]))
  f.addStep(Compile(workdir=WORKDIR + "/spotifyblob/blob", haltOnFailure=True, command=make_cmd + ["install", ZAPHOD_JOBS]))
  f.addStep(ShellCommand(name="strip", workdir=WORKDIR, haltOnFailure=True, command=schroot_cmd + ["sh", "-c", "strip spotify/version*/blob"]))
  f.addStep(OutputFinder(pattern="bin/spotify/version*-*bit"))
  f.addStep(SetProperty(command="echo " + SPOTIFYBASE, property="spotifybase"))
  f.addStep(MasterShellCommand(command=WithProperties("""
    mkdir %(spotifybase)s/%(output-filename)s || true;
    chmod 0775 %(spotifybase)s/%(output-filename)s || true;
    ln -s %(spotifybase)s/`echo %(output-filename)s | sed 's/.*-/common-/'`/* %(spotifybase)s/%(output-filename)s/ || true
  """)))
  f.addStep(FileUpload(
    mode=0644,
    slavesrc=WithProperties("bin/spotify/%(output-filename)s/blob"),
    masterdest=WithProperties(SPOTIFYBASE + "/%(output-filename)s/blob")))
  return f

def MakeDebBuilder(arch, dist, chroot=None, dist_type="ubuntu"):
  schroot_cmd = []
  if chroot is not None:
    schroot_cmd = ["schroot", "-p", "-c", chroot, "--"]

  cmake_cmd = schroot_cmd + ["cmake", "..",
    "-DWITH_DEBIAN=ON",
    "-DDEB_ARCH=" + arch,
    "-DDEB_DIST=" + dist,
    "-DENABLE_SPOTIFY_BLOB=OFF",
  ]
  make_cmd  = schroot_cmd + ["make", "deb", ZAPHOD_JOBS]

  f = factory.BuildFactory()
  f.addStep(Git(**GIT_ARGS))
  f.addStep(ShellCommand(name="cmake", command=cmake_cmd, haltOnFailure=True, workdir=WORKDIR))
  f.addStep(Compile(command=make_cmd, haltOnFailure=True, workdir=WORKDIR))
  f.addStep(OutputFinder(pattern="bin/clementine_*.deb"))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc=WithProperties("bin/%(output-filename)s"),
      masterdest=WithProperties(UPLOADBASE + "/" + dist_type + "-" + dist + "/%(output-filename)s")))
  return f

def MakeRpmBuilder(distro, arch, chroot, upload_ver):
  # Put /usr/bin first so we use the right mock
  env = dict(os.environ)
  env["PATH"] = "/usr/bin:" + env["PATH"]

  f = factory.BuildFactory()
  f.addStep(Git(**GIT_ARGS))
  f.addStep(ShellCommand(name="cmake", workdir=WORKDIR, haltOnFailure=True, command=[
      "cmake", "..",
      "-DRPM_DISTRO=" + distro,
      "-DRPM_ARCH=" + arch,
      "-DMOCK_CHROOT=" + chroot,
      "-DENABLE_SPOTIFY_BLOB=OFF",
  ]))
  f.addStep(Compile(command=["make", ZAPHOD_JOBS, "rpm"], workdir=WORKDIR, env=env, haltOnFailure=True))
  f.addStep(OutputFinder(pattern="bin/clementine-*.rpm"))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc=WithProperties("bin/%(output-filename)s"),
      masterdest=WithProperties(UPLOADBASE + "/fedora-" + upload_ver + "/%(output-filename)s")))
  return f

def MakeMingwBuilder(type, suffix):
  schroot_cmd = ["schroot", "-p", "-c", "mingw", "--"]

  test_env = dict(TEST_ENV)

  build_env = {'PKG_CONFIG_LIBDIR': '/target/lib/pkgconfig'}

  f = factory.BuildFactory()
  f.addStep(Git(**GIT_ARGS))
  f.addStep(ShellCommand(name="cmake", workdir=WORKDIR, env=build_env, haltOnFailure=True, command=schroot_cmd + [
      "cmake", "..",
      "-DCMAKE_TOOLCHAIN_FILE=/src/Toolchain-mingw32.cmake",
      "-DCMAKE_BUILD_TYPE=" + type,
      "-DQT_HEADERS_DIR=/target/include",
      "-DQT_LIBRARY_DIR=/target/bin",
      "-DPROTOBUF_PROTOC_EXECUTABLE=/target/bin/protoc",
  ]))
  f.addStep(ShellCommand(name="link dependencies", workdir=WORKDIR, haltOnFailure=True, command=schroot_cmd + [
      "sh", "-c",
      "ln -svf /src/windows/clementine-deps/* ../dist/windows/",
  ]))
  f.addStep(ShellCommand(name="link output", workdir="build/dist/windows", haltOnFailure=True, command=schroot_cmd + [
      "ln", "-svf", "../../bin/clementine.exe", "../../bin/clementine-spotifyblob.exe", ".",
  ]))
  f.addStep(ShellCommand(name="link test", workdir=WORKDIR, haltOnFailure=True, command=schroot_cmd + [
      "sh", "-c",
      "ln -svf /src/windows/clementine-deps/* tests/",
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
    'GTEST_FILTER': '-Formats/FileformatsTest.GstCanDecode*:SongLoaderTest.LoadRemote*',
  })

  f = factory.BuildFactory()
  f.addStep(Git(**GIT_ARGS))
  f.addStep(ShellCommand(
      name="cmake",
      workdir=WORKDIR,
      env={'PKG_CONFIG_PATH': '/target/lib/pkgconfig'},
      command=[
        "cmake", "..",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_OSX_SYSROOT=/Developer/SDKs/MacOSX10.6.sdk",
        "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.6",
				"-DCMAKE_OSX_ARCHITECTURES=i386",
				"-DBOOST_ROOT=/target",
        "-DPROTOBUF_LIBRARY=/target/lib/libprotobuf-lite.dylib",
        "-DPROTOBUF_INCLUDE_DIR=/target/include/",
        "-DPROTOBUF_PROTOC_EXECUTABLE=/target/bin/protoc",
        "-DSPOTIFY=/target/libspotify.framework",
        "-DGLEW_INCLUDE_DIRS=/target/include",
        "-DGLEW_LIBRARIES=/target/lib/libGLEW.dylib",
        "-DLASTFM_INCLUDE_DIRS=/target/include/",
        "-DLASTFM_LIBRARIES=/target/lib/liblastfm.dylib",
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
  schroot_cmd         = ["schroot", "-p", "-c", "mingw", "-d", "/src", "--"]
  schroot_cmd_workdir = ["schroot", "-p", "-c", "mingw", "-d", "/src/windows", "--"]

  f = factory.BuildFactory()
  f.addStep(ShellCommand(name="checkout", command=schroot_cmd + ["git", "pull"]))
  f.addStep(ShellCommand(name="clean", command=schroot_cmd_workdir + ["make", "clean"]))
  f.addStep(ShellCommand(name="compile", command=schroot_cmd_workdir + ["make"]))
  return f

def MakeMacDepsBuilder():
  src     = "/src"
  workdir = "/src/macosx"

  f = factory.BuildFactory()
  f.addStep(ShellCommand(name="checkout", workdir=src,     command=["git", "pull"]))
  f.addStep(ShellCommand(name="clean",    workdir=workdir, command=["make", "clean"]))
  f.addStep(ShellCommand(name="compile",  workdir=workdir, command=["make"]))
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
  BuilderDef("Linux GCC 4.6.0",  "clementine_linux_gcc460",  MakeLinuxBuilder('Release', gcc460=True)),
  BuilderDef("Linux Minimal",    "clementine_linux_minimal", MakeLinuxBuilder('Release', disable_everything=True)),
  BuilderDef("Spotify blob 32-bit", "clementine_spotify_32", MakeSpotifyBlobBuilder(chroot='lucid-32')),
  BuilderDef("Spotify blob 64-bit", "clementine_spotify_64", MakeSpotifyBlobBuilder()),
  BuilderDef("Deb Lucid 64-bit", "clementine_deb_lucid_64",  MakeDebBuilder('amd64', 'lucid')),
  BuilderDef("Deb Lucid 32-bit", "clementine_deb_lucid_32",  MakeDebBuilder('i386',  'lucid', chroot='lucid-32')),
  BuilderDef("Deb Maverick 64-bit", "clementine_deb_maverick_64", MakeDebBuilder('amd64', 'maverick', chroot='maverick-64')),
  BuilderDef("Deb Maverick 32-bit", "clementine_deb_maverick_32", MakeDebBuilder('i386',  'maverick', chroot='maverick-32')),
  BuilderDef("Deb Natty 64-bit", "clementine_deb_natty_64", MakeDebBuilder('amd64', 'natty', chroot='natty-64')),
  BuilderDef("Deb Natty 32-bit", "clementine_deb_natty_32", MakeDebBuilder('i386',  'natty', chroot='natty-32')),
  BuilderDef("Deb Squeeze 64-bit", "clementine_deb_squeeze_64", MakeDebBuilder('amd64', 'squeeze', chroot='squeeze-64', dist_type='debian')),
  BuilderDef("Deb Squeeze 32-bit", "clementine_deb_squeeze_32", MakeDebBuilder('i386',  'squeeze', chroot='squeeze-32', dist_type='debian')),
  BuilderDef("Rpm Fedora 13 64-bit", "clementine_rpm_fc13_64", MakeRpmBuilder('fc13', 'x86_64', 'fedora-13-x86_64', '13')),
  BuilderDef("Rpm Fedora 13 32-bit", "clementine_rpm_fc13_32", MakeRpmBuilder('fc13', 'i686',   'fedora-13-i386',   '13')),
  BuilderDef("Rpm Fedora 14 64-bit", "clementine_rpm_fc14_64", MakeRpmBuilder('fc14', 'x86_64', 'fedora-14-x86_64', '14')),
  BuilderDef("Rpm Fedora 14 32-bit", "clementine_rpm_fc14_32", MakeRpmBuilder('fc14', 'i686',   'fedora-14-i386',   '14')),
  BuilderDef("PPA Lucid",        "clementine_ppa",           MakePPABuilder('lucid')),
  BuilderDef("PPA Maverick",     "clementine_ppa_maverick",  MakePPABuilder('maverick', chroot='maverick-64')),
  BuilderDef("PPA Natty",        "clementine_ppa_natty",     MakePPABuilder('natty', chroot='natty-32')),
  BuilderDef("MinGW Debug",      "clementine_mingw_debug",   MakeMingwBuilder('Debug', 'debug')),
  BuilderDef("MinGW Release",    "clementine_mingw_release", MakeMingwBuilder('Release', 'release')),
  BuilderDef("Mac Release",      "clementine_mac_release",   MakeMacBuilder(), slave="zarquon"),
  BuilderDef("Dependencies Mingw", "clementine_mingw_deps",  MakeMinGWDepsBuilder()),
  BuilderDef("Dependencies Mac", "clementine_mac_deps",      MakeMacDepsBuilder(), slave="zarquon"),
]

