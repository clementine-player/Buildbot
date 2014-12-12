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
GITBASEURL  = "https://github.com/clementine-player/Clementine.git"
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
    BuildSlave("beeblebrox", clementine_passwords.BEEBLEBROX, max_builds=2, notify_on_missing="john.maguire@gmail.com"),
    BuildSlave("zarquon",    clementine_passwords.ZARQUON, notify_on_missing="me@davidsansome.com"),
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
      repourl="https://github.com/clementine-player/Website.git",
      pollinterval=60*5, # seconds
      branch='master',
      workdir="gitpoller_work_website",
    ),
    GitPoller(
      project="dependencies",
      repourl="https://github.com/clementine-player/Dependencies.git",
      pollinterval=60*5, # seconds
      branch='master',
      workdir="gitpoller_work_deps",
    ),
    GitPoller(
      project="android-remote",
      repourl="https://github.com/clementine-player/Android-Remote.git",
      pollinterval=60*5, # seconds
      branch='master',
      workdir="gitpoller_work_android_remote",
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
android_remote_change_filter = ChangeFilter(project="android-remote", branch=u"master")

# Schedulers
sched_linux = Scheduler(name="linux", change_filter=change_filter, treeStableTimer=2*60, builderNames=[
  "Linux Debug",
  "Linux Release",
  "Linux Minimal",
])

sched_winmac = Scheduler(name="winmac", change_filter=change_filter, treeStableTimer=2*60, builderNames=[
  "MinGW-w64 Debug",
  "MinGW-w64 Release",
  "Mac Release",
])

sched_deb = Dependent(name="deb", upstream=sched_linux, builderNames=[
  "Deb Jessie 64-bit",
  "Deb Jessie 32-bit",
  "Deb Precise 64-bit",
  "Deb Precise 32-bit",
  "Deb Trusty 64-bit",
  "Deb Trusty 32-bit",
  "Deb Utopic 64-bit",
  "Deb Utopic 32-bit",
])

sched_rpm = Dependent(name="rpm", upstream=sched_linux, builderNames=[
  "Rpm Fedora 19 64-bit",
  "Rpm Fedora 19 32-bit",
  "Rpm Fedora 20 64-bit",
  "Rpm Fedora 20 32-bit",
])

sched_pot = Dependent(name="pot", upstream=sched_linux, builderNames=[
  "Transifex POT push",
])

sched_website = Scheduler(name="website", change_filter=website_change_filter, treeStableTimer=2*60, builderNames=[
  "Transifex website POT push",
])

sched_ppa = Dependent(name="ppa", upstream=sched_deb, builderNames=[
  "PPA Precise",
  "PPA Trusty",
  "PPA Utopic",
])

sched_dependencies = Scheduler(name="dependencies", change_filter=deps_change_filter, treeStableTimer=2*60, builderNames=[
  "Dependencies Mingw-w64",
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
    "Transifex Android Remote PO pull",
  ],
)

sched_android_remote = Scheduler(name="android_remote", change_filter=android_remote_change_filter, treeStableTimer=2*60, builderNames=[
  "Android-Remote",
])

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
  sched_android_remote,
]


# Builders
def MakeLinuxBuilder(type, disable_everything=False, transifex_push=False):
  cmake_args = [
    "cmake", "..",
    "-DCMAKE_BUILD_TYPE=" + type,
  ]
  test_env = dict(TEST_ENV)

  if disable_everything:
    cmake_args += [
      "-DBUNDLE_PROJECTM_PRESETS=OFF",
      "-DENABLE_AUDIOCD=OFF",
      "-DENABLE_BOX=OFF",
      "-DENABLE_DBUS=OFF",
      "-DENABLE_DEVICEKIT=OFF",
      "-DENABLE_DROPBOX=OFF",
      "-DENABLE_GIO=OFF",
      "-DENABLE_GOOGLE_DRIVE=OFF",
      "-DENABLE_LIBGPOD=OFF",
      "-DENABLE_LIBLASTFM=OFF",
      "-DENABLE_LIBMTP=OFF",
      "-DENABLE_LIBPULSE=OFF",
      "-DENABLE_MOODBAR=OFF",
      "-DENABLE_REMOTE=OFF",
      "-DENABLE_SEAFILE=OFF",
      "-DENABLE_SKYDRIVE=OFF",
      "-DENABLE_SOUNDMENU=OFF",
      "-DENABLE_SPARKLE=OFF",
      "-DENABLE_SPOTIFY=OFF",
      "-DENABLE_SPOTIFY_BLOB=OFF",
      "-DENABLE_VISUALISATIONS=OFF",
      "-DENABLE_VK=OFF",
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
  mock_cmd = "sudo;mock"

  if schroot is not None:
    schroot_cmd = ["schroot", "-p", "-c", schroot, "--"]

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

def MakeMingwBuilder(type, suffix, schroot, portable):
  schroot_cmd = ["schroot", "-p", "-c", schroot, "--"]

  test_env = dict(TEST_ENV)
  test_env.update({
    'GTEST_FILTER': '-' + ':'.join(DISABLED_TESTS + ['SongTest.*']),
  })

  build_env = {
    'PKG_CONFIG_LIBDIR': '/target/lib/pkgconfig',
    'PATH': '/mingw/bin:' + os.environ['PATH'],
  }

  executable_files = [
    "clementine.exe",
    "clementine-tagreader.exe",
    "clementine-spotifyblob.exe",
  ]

  strip_command = 'i686-w64-mingw32-strip'

  console = "OFF"
  if type == "Debug":
    console = "ON"
    type = ""

  f = factory.BuildFactory()
  f.addStep(Git(**GIT_ARGS))
  f.addStep(ShellCommand(name="cmake", workdir=WORKDIR, env=build_env, haltOnFailure=True, command=schroot_cmd + [
      "cmake", "..",
      "-DCMAKE_TOOLCHAIN_FILE=/src/Toolchain-mingw32.cmake",
      "-DCMAKE_BUILD_TYPE=" + type,
      "-DENABLE_WIN32_CONSOLE=" + console,
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
    f.addStep(ShellCommand(name="strip", workdir=WORKDIR, haltOnFailure=True, env=build_env, command=schroot_cmd + [
      strip_command] + executable_files))

  f.addStep(Test(workdir=WORKDIR, env=test_env, command=schroot_cmd + [
      "xvfb-run",
      "-a",
      "-n", "30",
      "make", "test"
  ]))
  if portable:
    f.addStep(ShellCommand(name="makensis", command=schroot_cmd + ["makensis", "clementine-portable.nsi"], workdir="build/dist/windows", haltOnFailure=True))
    f.addStep(OutputFinder(pattern="dist/windows/Clementine-PortableSetup*.exe"))
    f.addStep(FileUpload(
        mode=0644,
        slavesrc=WithProperties("dist/windows/%(output-filename)s"),
        masterdest=WithProperties(UPLOADBASE + "/win32/" + suffix + "/%(output-filename)s")))
  else:
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
        "-DCMAKE_OSX_ARCHITECTURES=x86_64",
        "-DBOOST_ROOT=/target",
        "-DPROTOBUF_LIBRARY=/target/lib/libprotobuf.dylib",
        "-DPROTOBUF_INCLUDE_DIR=/target/include/",
        "-DPROTOBUF_PROTOC_EXECUTABLE=/target/bin/protoc",
        "-DQT_QMAKE_EXECUTABLE=/target/bin/qmake",
        "-DSPOTIFY=/target/libspotify.framework",
        "-DGLEW_INCLUDE_DIRS=/target/include",
        "-DGLEW_LIBRARIES=/target/lib/libGLEW.dylib",
        "-DLASTFM_INCLUDE_DIRS=/target/include/",
        "-DLASTFM_LIBRARIES=/target/lib/liblastfm.dylib",
        "-DFFTW3_DIR=/target",
        "-DCMAKE_INCLUDE_PATH=/target/include",
        "-DAPPLE_DEVELOPER_ID='Developer ID Application: John Maguire (CZ8XD8GTGZ)'",
      ],
      haltOnFailure=True,
  ))
  f.addStep(Compile(command=["make"], workdir=WORKDIR, haltOnFailure=True))
#  f.addStep(Test(
#      command=["make", "test"],
#      workdir=WORKDIR,
#      env=TEST_ENV))
  f.addStep(ShellCommand(name="install", command=["make", "install"], haltOnFailure=True, workdir=WORKDIR))
  f.addStep(ShellCommand(name="sign", command=["make", "sign"], haltOnFailure=True, workdir=WORKDIR))
  f.addStep(ShellCommand(name="dmg", command=["make", "dmg"], haltOnFailure=True, workdir=WORKDIR))
  f.addStep(OutputFinder(pattern="bin/clementine-*.dmg"))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc=WithProperties("bin/%(output-filename)s"),
      masterdest=WithProperties(UPLOADBASE + "/mac/%(output-filename)s")))
  return f

def MakeAndroidRemoteBuilder():
  f = factory.BuildFactory()
  git_args = dict(GIT_ARGS)
  git_args["repourl"] = "https://github.com/clementine-player/Android-Remote.git"
  f.addStep(Git(**git_args))

# Change path to properties file here
  replace = "s:key.properties:/var/lib/buildbot/properties.txt:g"
  f.addStep(ShellCommand(name="sed", command=["sed", '-i', '-e', replace, "app/build.gradle"], haltOnFailure=True, workdir='build'))

  f.addStep(ShellCommand(name="compile", command=["./gradlew", "assembleRelease"], haltOnFailure=True, workdir='build'))
  f.addStep(OutputFinder(pattern="app/build/outputs/apk/ClementineRemote-release-*.apk"))
  f.addStep(FileUpload(
      mode=0644,
      slavesrc=WithProperties("app/build/outputs/apk/%(output-filename)s"),
      masterdest=WithProperties(UPLOADBASE + "/android/%(output-filename)s")))
  return f

def MakePPABuilder(dist, chroot=None):
  schroot_cmd = []
  if chroot is not None:
    schroot_cmd = ["schroot", "-p", "-c", chroot, "--"]

  ppa_env = {'DIST': dist}

  f = factory.BuildFactory()
  f.addStep(ShellCommand(command=schroot_cmd + ["/var/lib/buildbot/uploadtoppa.sh"],
    name="upload",
    env=ppa_env,
    workdir="build",
  ))
  return f

def MakeMinGWDepsBuilder(schroot_name):
  schroot_cmd         = ["schroot", "-p", "-c", schroot_name, "-d", "/src", "--"]
  schroot_cmd_workdir = ["schroot", "-p", "-c", schroot_name, "-d", "/src/windows", "--"]

  env = {'PATH': '/mingw/bin:' + os.environ['PATH']}

  f = factory.BuildFactory()
  f.addStep(ShellCommand(name="checkout", command=schroot_cmd + ["git", "pull"]))
  f.addStep(ShellCommand(name="clean", command=schroot_cmd_workdir + ["make", "clean"]))
  f.addStep(ShellCommand(name="compile", command=schroot_cmd_workdir + ["make"], env=env))
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

  f.addStep(ShellCommand(name="tx_init", workdir="build", haltOnFailure=True, command=["tx", "init", "--host=https://www.transifex.com"]))
  f.addStep(ShellCommand(name="tx_set",  workdir="build", haltOnFailure=True, command=set_args))

def AddClementineTxSetup(f, pot=True):
  AddTxSetup(f, "clementine.clementineplayer",
      "src/translations/translations.pot",
      "src/translations/<lang>.po", pot)

def AddWebsiteTxSetup(f):
  AddTxSetup(f, "clementine.website",
      "www.clementine-player.org/locale/django.pot",
      "www.clementine-player.org/locale/<lang>.po")

def AddAndroidRemoteTxSetup(f, pot=True):
  AddTxSetup(f, "clementine-remote.clementine-remote",
      "app/res/values/strings.xml",
      "app/res/values-<lang>/strings.xml")

def MakeWebsiteTransifexPotPushBuilder():
  f = factory.BuildFactory()
  git_args = dict(GIT_ARGS)
  git_args["repourl"] = "https://github.com/clementine-player/Website.git"
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
    "--message=Automatic merge of translations from Transifex (https://www.transifex.com/projects/p/clementine/resource/clementineplayer)"
  ]))
  f.addStep(ShellCommand(name="git_push",   workdir="build", haltOnFailure=True, command=["git", "push", "git@github.com:clementine-player/Clementine.git", "master", "--verbose"]))
  return f


def MakeWebsiteTransifexPoPullBuilder():
  f = factory.BuildFactory()
  git_args = dict(GIT_ARGS)
  git_args["repourl"] = "git@github.com:clementine-player/Website.git"
  f.addStep(Git(**git_args))
  AddWebsiteTxSetup(f)
  f.addStep(ShellCommand(name="tx_pull", workdir="build", haltOnFailure=True,
                         command=["tx", "pull", "-a", "--force"]))
  f.addStep(ShellCommand(name="git_add", workdir="build", haltOnFailure=True, command="git add --verbose www.clementine-player.org/locale/*.po"))
  f.addStep(ShellCommand(name="git_commit", workdir="build", haltOnFailure=True, command=["git", "commit", "--author=Clementine Buildbot <buildbot@clementine-player.org>", "--message=Automatic merge of translations from Transifex (https://www.transifex.com/projects/p/clementine/resource/website)"]))
  f.addStep(ShellCommand(name="git_push",   workdir="build", haltOnFailure=True, command=["git", "push", "git@github.com:clementine-player/Website.git", "master", "--verbose"]))
  return f

def MakeAndroidRemoteTransifexPoPullBuilder():
  f = factory.BuildFactory()
  git_args = dict(GIT_ARGS)
  git_args["repourl"] = "https://github.com/clementine-player/Android-Remote.git"
  f.addStep(Git(**git_args))
  AddAndroidRemoteTxSetup(f)
  f.addStep(ShellCommand(name="tx_pull", workdir="build", haltOnFailure=True,
                         command=["tx", "pull", "-a", "--force"]))
  f.addStep(ShellCommand(name="git_add", workdir="build", haltOnFailure=True, command="git add --verbose app/res/values-*"))
  f.addStep(ShellCommand(name="git_commit", workdir="build", haltOnFailure=True, command=["git", "commit", "--author=Clementine Buildbot <buildbot@clementine-player.org>", "--message=Automatic merge of translations from Transifex (https://www.transifex.com/projects/p/clementine-remote/resource/clementine-remote)"]))
  f.addStep(ShellCommand(name="git_push",   workdir="build", haltOnFailure=True, command=["git", "push", "git@github.com:clementine-player/Android-Remote.git", "master", "--verbose"]))
  return f


def BuilderDef(name, dir, factory, slave="beeblebrox"):
  return {
    'name': name,
    'builddir': dir,
    'factory': factory,
    'slavename': slave,
  }

c['builders'] = [
  BuilderDef("Linux Debug",      "clementine_linux_debug",   MakeLinuxBuilder('Debug')),
  BuilderDef("Linux Release",    "clementine_linux_release", MakeLinuxBuilder('Release')),
  BuilderDef("Linux Minimal",    "clementine_linux_minimal", MakeLinuxBuilder('Release', disable_everything=True)),
  BuilderDef("Spotify blob 32-bit", "clementine_spotify_32", MakeSpotifyBlobBuilder(chroot='precise-32')),
  BuilderDef("Spotify blob 64-bit", "clementine_spotify_64", MakeSpotifyBlobBuilder()),
  BuilderDef("Deb Precise 64-bit", "clementine_deb_precise_64", MakeDebBuilder('amd64', 'precise')),
  BuilderDef("Deb Precise 32-bit", "clementine_deb_precise_32", MakeDebBuilder('i386',  'precise', chroot='precise-32')),
  BuilderDef("Deb Trusty 64-bit", "clementine_deb_trusty_64", MakeDebBuilder('amd64',  'trusty', chroot='trusty-64')),
  BuilderDef("Deb Trusty 32-bit", "clementine_deb_trusty_32", MakeDebBuilder('i386',  'trusty', chroot='trusty-32')),
  BuilderDef("Deb Utopic 64-bit", "clementine_deb_utopic_64", MakeDebBuilder('amd64',  'utopic', chroot='utopic-64')),
  BuilderDef("Deb Utopic 32-bit", "clementine_deb_utopic_32", MakeDebBuilder('i386',  'utopic', chroot='utopic-32')),
  BuilderDef("Deb Jessie 64-bit",  "clementine_deb_jessie_64", MakeDebBuilder('amd64', 'jessie', chroot='jessie-64', dist_type='debian')),
  BuilderDef("Deb Jessie 32-bit",  "clementine_deb_jessie_32", MakeDebBuilder('i386',  'jessie', chroot='jessie-32', dist_type='debian')),
  BuilderDef("Rpm Fedora 19 64-bit", "clementine_rpm_fc19_64", MakeRpmBuilder('fc19', 'x86_64', 'fedora-19-x86_64', '19')),
  BuilderDef("Rpm Fedora 19 32-bit", "clementine_rpm_fc19_32", MakeRpmBuilder('fc19', 'i686',   'fedora-19-i386',   '19')),
  BuilderDef("Rpm Fedora 20 64-bit", "clementine_rpm_fc20_64", MakeRpmBuilder('fc20', 'x86_64', 'fedora-20-x86_64', '20')),
  BuilderDef("Rpm Fedora 20 32-bit", "clementine_rpm_fc20_32", MakeRpmBuilder('fc20', 'i686',   'fedora-20-i386',   '20')),
  BuilderDef("Transifex POT push", "clementine_pot_upload",  MakeLinuxBuilder('Release', disable_everything=True, transifex_push=True)),
  BuilderDef("Transifex PO pull", "clementine_po_pull",      MakeTransifexPoPullBuilder()),
  BuilderDef("Transifex website POT push", "website_pot_upload", MakeWebsiteTransifexPotPushBuilder()),
  BuilderDef("Transifex website PO pull", "website_po_pull", MakeWebsiteTransifexPoPullBuilder()),
  BuilderDef("Transifex Android Remote PO pull", "android_remote_po_pull", MakeAndroidRemoteTransifexPoPullBuilder()),
  BuilderDef("PPA Precise",      "clementine_ppa_precise",   MakePPABuilder('precise', chroot='precise-32')),
  BuilderDef("PPA Trusty",       "clementine_ppa_trusty",    MakePPABuilder('trusty',  chroot='trusty-32')),
  BuilderDef("PPA Utopic",       "clementine_ppa_utopic",    MakePPABuilder('utopic',  chroot='utopic-32')),
  BuilderDef("Mac Release",      "clementine_mac_release",   MakeMacBuilder(), slave="zarquon"),
  BuilderDef("Dependencies Mac", "clementine_mac_deps",      MakeMacDepsBuilder(), slave="zarquon"),

  BuilderDef("Dependencies Mingw-w64", "clementine_mingw_w64_deps",  MakeMinGWDepsBuilder("mingw")),
  BuilderDef("MinGW-w64 Release",    "clementine_mingw_w64_release", MakeMingwBuilder('Release', 'release', 'mingw', False)),
  BuilderDef("MinGW-w64 Debug",    "clementine_mingw_w64_debug", MakeMingwBuilder('Debug', 'debug', 'mingw', False)),
  BuilderDef("MinGW-w64 Portable",    "clementine_mingw_w64_portable", MakeMingwBuilder('Release', 'release', 'mingw', True)),

  BuilderDef("Android-Remote", "android-remote", MakeAndroidRemoteBuilder())
]
