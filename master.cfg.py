# -*- python -*-
# ex: set syntax=python:

from buildbot.buildslave import BuildSlave
from buildbot.changes.gitpoller import GitPoller
from buildbot.process import factory
from buildbot.process.properties import WithProperties
from buildbot.scheduler import Scheduler, Dependent
from buildbot.schedulers.filter import ChangeFilter
from buildbot.schedulers.timed import Nightly
from buildbot.status import html, mail, web
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

# Authentication
authz = web.authz.Authz(
  auth=web.auth.BasicAuth(clementine_passwords.WEB_USERS),
  forceBuild="auth",
  forceAllBuilds="auth",
  pingBuilder="auth",
  gracefulShutdown="auth",
  stopBuild="auth",
  stopAllBuilds="auth",
  cancelPendingBuild="auth",
  stopChange="auth",
  cleanShutdown="auth",
)

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
      project="clementine",
      repourl=GITBASEURL,
      pollinterval=60*5, # seconds
      branch='master',
      workdir="gitpoller_work",
    ),
    GitPoller(
      project="website",
      repourl="https://code.google.com/p/clementine-player.appengine/",
      pollinterval=60*5, # seconds
      branch='master',
      workdir="gitpoller_work_website",
    ),
    GitPoller(
      project="dependencies",
      repourl="https://code.google.com/p/clementine-player.dependencies/",
      pollinterval=60*5, # seconds
      branch='master',
      workdir="gitpoller_work_deps",
    ),
  ],
  'status': [
    html.WebStatus(
      http_port="tcp:8010:interface=127.0.0.1",
      authz=authz,
    ),
    mail.MailNotifier(
      fromaddr="buildmaster@zaphod.purplehatstands.com",
      lookup="gmail.com",
      mode="failing",
    ),
  ],
}

change_filter = ChangeFilter(project="clementine", branch=u"master")
website_change_filter = ChangeFilter(project="website", branch=u"master")
deps_change_filter = ChangeFilter(project="dependencies", branch=u"master")

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
  "Deb Oneiric 64-bit",
  "Deb Oneiric 32-bit",
  "Deb Wheezy 64-bit",
  "Deb Wheezy 32-bit",
  "Deb Precise 64-bit",
  "Deb Precise 32-bit",
])

sched_rpm = Dependent(name="rpm", upstream=sched_linux, builderNames=[
  "Rpm Fedora 16 64-bit",
  "Rpm Fedora 16 32-bit",
  "Rpm Fedora 17 64-bit",
  "Rpm Fedora 17 32-bit",
])

sched_pot = Dependent(name="pot", upstream=sched_linux, builderNames=[
  "Transifex POT push",
])

sched_website = Scheduler(name="website", change_filter=website_change_filter, treeStableTimer=2*60, builderNames=[
  "Transifex website POT push",
])

sched_ppa = Dependent(name="ppa", upstream=sched_deb, builderNames=[
  "PPA Lucid",
  "PPA Maverick",
  "PPA Natty",
  "PPA Oneiric",
  "PPA Precise",
])

sched_dependencies = Scheduler(name="dependencies", change_filter=deps_change_filter, treeStableTimer=2*60, builderNames=[
  "Dependencies Mingw",
  "Dependencies Mac",
])

sched_spotifyblob = Dependent(name="spotifyblob", upstream=sched_linux, builderNames=[
  "Spotify blob 32-bit",
  "Spotify blob 64-bit",
])

sched_transifex_pull = Nightly(name="transifex_pull",
  change_filter=change_filter,
  hour=10,
  minute=0,
  dayOfWeek=0,
  branch="master",
  builderNames=[
    "Transifex PO pull",
    "Transifex website PO pull",
  ],
)

c['schedulers'] = [
  sched_linux,
  sched_winmac,
  sched_deb,
  sched_rpm,
  sched_pot,
  sched_ppa,
  sched_dependencies,
  sched_spotifyblob,
  sched_transifex_pull,
  sched_website,
]


# Builders
def MakeLinuxBuilder(type, clang=False, gcc460=False, disable_everything=False, transifex_push=False):
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
      "-DENABLE_AUDIOCD=OFF",
      "-DENABLE_DBUS=OFF",
      "-DENABLE_DEVICEKIT=OFF",
      "-DENABLE_GIO=OFF",
      "-DENABLE_IMOBILEDEVICE=OFF",
      "-DENABLE_LIBGPOD=OFF",
      "-DENABLE_LIBLASTFM=OFF",
      "-DENABLE_LIBMTP=OFF",
      "-DENABLE_MOODBAR=OFF",
      "-DENABLE_REMOTE=OFF",
      "-DENABLE_SCRIPTING_ARCHIVES=OFF",
      "-DENABLE_SCRIPTING_PYTHON=OFF",
      "-DENABLE_SOUNDMENU=OFF",
      "-DENABLE_SPARKLE=OFF",
      "-DENABLE_SPOTIFY=OFF",
      "-DENABLE_SPOTIFY_BLOB=OFF",
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

  if transifex_push:
    AddClementineTxSetup(f)
    f.addStep(ShellCommand(name="tx_push", workdir="build", haltOnFailure=True, command=["tx", "push", "-s"]))
  else:
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
  f.addStep(Compile(workdir=WORKDIR + "/ext/clementine-spotifyblob", haltOnFailure=True, command=make_cmd + ["install", ZAPHOD_JOBS]))
  f.addStep(ShellCommand(name="strip", workdir=WORKDIR, haltOnFailure=True, command=schroot_cmd + ["sh", "-c", "strip spotify/version*/blob"]))
  f.addStep(OutputFinder(pattern="bin/spotify/version*-*bit"))
  f.addStep(SetProperty(command="echo " + SPOTIFYBASE, property="spotifybase"))
  f.addStep(MasterShellCommand(name="verify", command=WithProperties("""
    openssl dgst -sha1 -verify %(spotifybase)s/clementine-spotify-public.pem \
      -signature %(spotifybase)s/%(output-filename)s/blob.sha1 \
      %(spotifybase)s/%(output-filename)s/blob
  """)))
  return f

def MakeDebBuilder(arch, dist, chroot=None, dist_type="ubuntu"):
  schroot_cmd = []
  if chroot is not None:
    schroot_cmd = ["schroot", "-p", "-c", chroot, "--"]

  env = dict(os.environ)
  env["DEB_BUILD_OPTIONS"] = 'parallel=4'

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
  f.addStep(Compile(command=make_cmd, haltOnFailure=True, workdir=WORKDIR, env=env))
  f.addStep(OutputFinder(pattern="bin/clementine_*.deb"))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc=WithProperties("bin/%(output-filename)s"),
      masterdest=WithProperties(UPLOADBASE + "/" + dist_type + "-" + dist + "/%(output-filename)s")))
  return f

def MakeRpmBuilder(distro, arch, chroot, upload_ver, schroot=None):
  schroot_cmd = []
  mock_cmd = "/usr/bin/mock"
  if schroot is not None:
    schroot_cmd = ["schroot", "-p", "-c", schroot, "--"]
    mock_cmd = "sudo;mock"

  f = factory.BuildFactory()
  f.addStep(Git(**GIT_ARGS))
  f.addStep(ShellCommand(name="cmake", workdir=WORKDIR, haltOnFailure=True, command=schroot_cmd + [
      "cmake", "..",
      "-DRPM_DISTRO=" + distro,
      "-DRPM_ARCH=" + arch,
      "-DMOCK_CHROOT=" + chroot,
      "-DMOCK_COMMAND=" + mock_cmd,
      "-DENABLE_SPOTIFY_BLOB=OFF",
  ]))
  f.addStep(Compile(command=schroot_cmd + ["make", ZAPHOD_JOBS, "rpm"], workdir=WORKDIR, haltOnFailure=True))
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

  executable_files = [
    "clementine.exe",
    "clementine-tagreader.exe",
    "clementine-spotifyblob.exe",
  ]

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
      "ln", "-svf"] + ["../../bin/" + x for x in executable_files] + ["."]))
  f.addStep(ShellCommand(name="link test", workdir=WORKDIR, haltOnFailure=True, command=schroot_cmd + [
      "sh", "-c",
      "ln -svf /src/windows/clementine-deps/* tests/",
  ]))
  f.addStep(Compile(command=schroot_cmd + ["make", ZAPHOD_JOBS], workdir=WORKDIR, haltOnFailure=True))

  if type != "Debug":
    f.addStep(ShellCommand(name="strip", workdir=WORKDIR, haltOnFailure=True, command=schroot_cmd + [
      "i586-mingw32msvc-strip"] + executable_files))

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
        "-DCMAKE_C_COMPILER=/target/clang-3.1/bin/clang",
        "-DCMAKE_CXX_COMPILER=/target/clang-3.1/bin/clang++",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_OSX_SYSROOT=/Developer/SDKs/MacOSX10.6.sdk",
        "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.6",
        "-DCMAKE_OSX_ARCHITECTURES=x86_64",
        "-DBOOST_ROOT=/target",
        "-DPROTOBUF_LIBRARY=/target/lib/libprotobuf-lite.dylib",
        "-DPROTOBUF_INCLUDE_DIR=/target/include/",
        "-DPROTOBUF_PROTOC_EXECUTABLE=/target/bin/protoc",
        "-DSPOTIFY=/target/libspotify.framework",
        "-DGLEW_INCLUDE_DIRS=/target/include",
        "-DGLEW_LIBRARIES=/target/lib/libGLEW.dylib",
        "-DLASTFM_INCLUDE_DIRS=/target/include/",
        "-DLASTFM_LIBRARIES=/target/lib/liblastfm.dylib",
        "-DFFTW3_DIR=/target",
        "-DCMAKE_INCLUDE_DIR=/target/include",
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

def AddTxSetup(f, resource, source_file, pattern, pot=True):
  set_args = [
      "tx", "set", "--auto-local", "-r", resource, pattern,
      "--source-lang", "en", "--execute"]

  if pot:
    set_args += ["--source-file", source_file]

  f.addStep(ShellCommand(name="tx_init", workdir="build", haltOnFailure=True, command=["tx", "init", "--host=https://www.transifex.net"]))
  f.addStep(ShellCommand(name="tx_set",  workdir="build", haltOnFailure=True, command=set_args))

def AddClementineTxSetup(f, pot=True):
  AddTxSetup(f, "clementine.clementineplayer",
      "src/translations/translations.pot",
      "src/translations/<lang>.po", pot)

def AddWebsiteTxSetup(f):
  AddTxSetup(f, "clementine.website",
      "www.clementine-player.org/locale/django.pot",
      "www.clementine-player.org/locale/<lang>.po")

def MakeWebsiteTransifexPotPushBuilder():
  f = factory.BuildFactory()
  git_args = dict(GIT_ARGS)
  git_args["repourl"] = "https://code.google.com/p/clementine-player.appengine/"
  f.addStep(Git(**git_args))
  AddWebsiteTxSetup(f)
  f.addStep(ShellCommand(name="tx_push", workdir="build", haltOnFailure=True, command=["tx", "push", "-s"]))
  return f

def MakeTransifexPoPullBuilder():
  f = factory.BuildFactory()
  f.addStep(Git(**GIT_ARGS))
  AddClementineTxSetup(f, pot=False)
  f.addStep(ShellCommand(name="tx_pull",    workdir="build", haltOnFailure=True,
                         command=["tx", "pull", "-a", "--force"]))
  f.addStep(ShellCommand(name="git_add",    workdir="build", haltOnFailure=True, command="git add --verbose src/translations/*.po"))
  f.addStep(ShellCommand(name="git_commit", workdir="build", haltOnFailure=True, command=[
    "git", "commit", "--author=Clementine Buildbot <buildbot@clementine-player.org>",
    "--message=Automatic merge of translations from Transifex (https://www.transifex.net/projects/p/clementine/resource/clementineplayer)"
  ]))
  f.addStep(ShellCommand(name="git_push",   workdir="build", haltOnFailure=True, command=["git", "push", GITBASEURL, "master", "--verbose"]))
  return f


def MakeWebsiteTransifexPoPullBuilder():
  f = factory.BuildFactory()
  git_args = dict(GIT_ARGS)
  git_args["repourl"] = "https://code.google.com/p/clementine-player.appengine/"
  f.addStep(Git(**git_args))
  AddWebsiteTxSetup(f)
  f.addStep(ShellCommand(name="tx_pull", workdir="build", haltOnFailure=True,
                         command=["tx", "pull", "-a", "--force"]))
  f.addStep(ShellCommand(name="git_add", workdir="build", haltOnFailure=True, command="git add --verbose www.clementine-player.org/locale/*.po"))
  f.addStep(ShellCommand(name="git_commit", workdir="build", haltOnFailure=True, command=["git", "commit", "--author=Clementine Buildbot <buildbot@clementine-player.org>", "--message=Automatic merge of translations from Transifex (https://www.transifex.net/projects/p/clementine/resource/website)"]))
  f.addStep(ShellCommand(name="git_push",   workdir="build", haltOnFailure=True, command=["git", "push", "https://code.google.com/p/clementine-player.appengine/", "master", "--verbose"]))
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
  BuilderDef("Deb Oneiric 64-bit", "clementine_deb_oneiric_64", MakeDebBuilder('amd64', 'oneiric', chroot='oneiric-64')),
  BuilderDef("Deb Oneiric 32-bit", "clementine_deb_oneiric_32", MakeDebBuilder('i386',  'oneiric', chroot='oneiric-32')),
  BuilderDef("Deb Precise 64-bit", "clementine_deb_precise_64", MakeDebBuilder('amd64', 'precise', chroot='precise-64')),
  BuilderDef("Deb Precise 32-bit", "clementine_deb_precise_32", MakeDebBuilder('i386',  'precise', chroot='precise-32')),
  BuilderDef("Deb Squeeze 64-bit", "clementine_deb_squeeze_64", MakeDebBuilder('amd64', 'squeeze', chroot='squeeze-64', dist_type='debian')),
  BuilderDef("Deb Squeeze 32-bit", "clementine_deb_squeeze_32", MakeDebBuilder('i386',  'squeeze', chroot='squeeze-32', dist_type='debian')),
  BuilderDef("Deb Wheezy 64-bit",  "clementine_deb_wheezy_64", MakeDebBuilder('amd64', 'wheezy', chroot='wheezy-64', dist_type='debian')),
  BuilderDef("Deb Wheezy 32-bit",  "clementine_deb_wheezy_32", MakeDebBuilder('i386',  'wheezy', chroot='wheezy-32', dist_type='debian')),
  BuilderDef("Rpm Fedora 13 64-bit", "clementine_rpm_fc13_64", MakeRpmBuilder('fc13', 'x86_64', 'fedora-13-x86_64', '13')),
  BuilderDef("Rpm Fedora 13 32-bit", "clementine_rpm_fc13_32", MakeRpmBuilder('fc13', 'i686',   'fedora-13-i386',   '13')),
  BuilderDef("Rpm Fedora 14 64-bit", "clementine_rpm_fc14_64", MakeRpmBuilder('fc14', 'x86_64', 'fedora-14-x86_64', '14')),
  BuilderDef("Rpm Fedora 14 32-bit", "clementine_rpm_fc14_32", MakeRpmBuilder('fc14', 'i686',   'fedora-14-i386',   '14')),
  BuilderDef("Rpm Fedora 15 64-bit", "clementine_rpm_fc15_64", MakeRpmBuilder('fc15', 'x86_64', 'fedora-15-x86_64', '15', "oneiric-64")),
  BuilderDef("Rpm Fedora 15 32-bit", "clementine_rpm_fc15_32", MakeRpmBuilder('fc15', 'i686',   'fedora-15-i386',   '15', "oneiric-64")),
  BuilderDef("Rpm Fedora 16 64-bit", "clementine_rpm_fc16_64", MakeRpmBuilder('fc16', 'x86_64', 'fedora-16-x86_64', '16', "oneiric-64")),
  BuilderDef("Rpm Fedora 16 32-bit", "clementine_rpm_fc16_32", MakeRpmBuilder('fc16', 'i686',   'fedora-16-i386',   '16', "oneiric-64")),
  BuilderDef("Rpm Fedora 17 64-bit", "clementine_rpm_fc17_64", MakeRpmBuilder('fc17', 'x86_64', 'fedora-17-x86_64', '17', "oneiric-64")),
  BuilderDef("Rpm Fedora 17 32-bit", "clementine_rpm_fc17_32", MakeRpmBuilder('fc17', 'i686',   'fedora-17-i386',   '17', "oneiric-64")),
  BuilderDef("Transifex POT push", "clementine_pot_upload",  MakeLinuxBuilder('Release', disable_everything=True, transifex_push=True)),
  BuilderDef("Transifex PO pull", "clementine_po_pull",      MakeTransifexPoPullBuilder()),
  BuilderDef("Transifex website POT push", "website_pot_upload", MakeWebsiteTransifexPotPushBuilder()),
  BuilderDef("Transifex website PO pull", "website_po_pull", MakeWebsiteTransifexPoPullBuilder()),
  BuilderDef("PPA Lucid",        "clementine_ppa",           MakePPABuilder('lucid')),
  BuilderDef("PPA Maverick",     "clementine_ppa_maverick",  MakePPABuilder('maverick', chroot='maverick-64')),
  BuilderDef("PPA Natty",        "clementine_ppa_natty",     MakePPABuilder('natty', chroot='natty-32')),
  BuilderDef("PPA Oneiric",      "clementine_ppa_oneiric",   MakePPABuilder('oneiric', chroot='oneiric-32')),
  BuilderDef("PPA Precise",      "clementine_ppa_precise",   MakePPABuilder('precise', chroot='precise-32')),
  BuilderDef("MinGW Debug",      "clementine_mingw_debug",   MakeMingwBuilder('Debug', 'debug')),
  BuilderDef("MinGW Release",    "clementine_mingw_release", MakeMingwBuilder('Release', 'release')),
  BuilderDef("Mac Release",      "clementine_mac_release",   MakeMacBuilder(), slave="zarquon"),
  BuilderDef("Dependencies Mingw", "clementine_mingw_deps",  MakeMinGWDepsBuilder()),
  BuilderDef("Dependencies Mac", "clementine_mac_deps",      MakeMacDepsBuilder(), slave="zarquon"),
]
