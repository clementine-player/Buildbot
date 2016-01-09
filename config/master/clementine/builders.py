import os.path

from buildbot.changes import gitpoller
from buildbot.plugins import util
from buildbot.process import factory
from buildbot.steps import master
from buildbot.steps import shell
from buildbot.steps import transfer
from buildbot.steps.source import git

SPOTIFYBASE = "/var/www/clementine-player.org/spotify"
UPLOADBASE  = "/var/www/clementine-player.org/builds"
UPLOADURL   = "http://builds.clementine-player.org"


def GitBaseUrl(repository):
  return "https://github.com/clementine-player/%s.git" % repository


def GitArgs(repository):
  return {
    "repourl": GitBaseUrl(repository),
    "branch": "master",
    "mode": "incremental",
    "retry": (5*60, 3),
    "workdir": "source",
  }


def GitPoller(repository):
  return gitpoller.GitPoller(
      project=repository.lower(),
      repourl=GitBaseUrl(repository),
      pollinterval=60*5, # seconds
      branch='master',
      workdir="gitpoller_%s" % repository.lower())


class OutputFinder(shell.ShellCommand):
  def __init__(self, pattern=None, **kwargs):
    if pattern is None:
      shell.ShellCommand.__init__(self, **kwargs)
    else:
      shell.ShellCommand.__init__(self,
        name="get output filename",
        command=["sh", "-c",
          "ls -dt " + pattern + " | grep -v debuginfo | head -n 1"],
        workdir="source",
        **kwargs
      )

  def commandComplete(self, cmd):
    filename = self.getLog('stdio').readlines()[0].strip()
    self.setProperty("output-filepath", filename)
    self.setProperty("output-filename", os.path.basename(filename))


def UploadPackage(directory):
  return transfer.FileUpload(
      mode=0644,
      workdir="source",
      slavesrc=util.Interpolate("%(prop:output-filepath)s"),
      masterdest=util.Interpolate(
          '%(kw:base)s/%(kw:directory)s/%(prop:output-filename)s',
          base=UPLOADBASE,
          directory=directory),
      url=util.Interpolate(
          '%(kw:base)s/%(kw:directory)s/%(prop:output-filename)s',
          base=UPLOADURL,
          directory=directory))


def MakeDebBuilder(distro, version, is_64_bit):
  arch = 'amd64' if is_64_bit else 'i386'

  env = {
    "DEB_BUILD_OPTIONS": 'parallel=4',
  }

  cmake_cmd = [
    "cmake", "..",
    "-DWITH_DEBIAN=ON",
    "-DDEB_ARCH=" + arch,
    "-DDEB_DIST=" + version,
    "-DFORCE_GIT_REVISION=",
    "-DENABLE_SPOTIFY_BLOB=OFF",
  ]
  make_cmd = ["make", "deb"]

  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Clementine")))
  f.addStep(shell.ShellCommand(name="cmake", command=cmake_cmd, haltOnFailure=True, workdir="source/bin"))
  f.addStep(shell.Compile(command=make_cmd, haltOnFailure=True, workdir="source/bin", env=env))
  f.addStep(OutputFinder(pattern="bin/clementine_*.deb"))
  f.addStep(UploadPackage('%s-%s' % (distro, version)))
  return f


def MakePPABuilder(distro, ppa):
  git_args = GitArgs("Clementine")
  git_args['mode'] = 'full'

  cmake_cmd = [
    "cmake", "..",
    "-DWITH_DEBIAN=ON",
    "-DDEB_DIST=" + distro,
  ]
  clean_cmd = "rm -rvf *.diff.*z *.tar.*z *.dsc *_source.changes source/bin/*"
  buildpackage_cmd = ["dpkg-buildpackage", "-S", "-kF6ABD82E"]
  movetarball_cmd = "mv -v source/dist/*.orig.tar.xz ."
  cleanuptarball_cmd = "rm -rfv source/dist/*.tar.*z source/.git"
  keys_cmd = "gpg --import /config/ppa-keys || true"
  dput_cmd = "dput %s *_source.changes" % ppa

  f = factory.BuildFactory()
  f.addStep(git.Git(**git_args))
  f.addStep(shell.ShellCommand(name="cmake", command=cmake_cmd, haltOnFailure=True, workdir="source/bin"))
  f.addStep(shell.ShellCommand(name="clean", command=clean_cmd, haltOnFailure=True, workdir="."))
  f.addStep(shell.ShellCommand(name="maketarball", command=["./maketarball.sh"], haltOnFailure=True, workdir="source/dist"))
  f.addStep(shell.ShellCommand(name="movetarball", command=movetarball_cmd, haltOnFailure=True, workdir="."))
  f.addStep(shell.ShellCommand(name="cleanuptarball", command=cleanuptarball_cmd, haltOnFailure=True, workdir="."))
  f.addStep(shell.ShellCommand(name="keys", command=keys_cmd, workdir="."))
  f.addStep(shell.ShellCommand(name="buildpackage", command=buildpackage_cmd, haltOnFailure=True, workdir="source"))
  f.addStep(shell.ShellCommand(name="dput", command=dput_cmd, haltOnFailure=True, workdir="."))
  return f


def MakeWindowsDepsBuilder():
  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Dependencies")))
  f.addStep(shell.ShellCommand(name="clean", workdir="source/windows", command=["make", "clean"]))
  f.addStep(shell.ShellCommand(name="compile", workdir="source/windows", command=["make"]))
  return f


def MakeWindowsBuilder(is_debug, is_portable):
  env = {
    'PKG_CONFIG_LIBDIR': '/target/lib/pkgconfig',
    'PATH': ':'.join([
        '/mingw/bin',
        '/usr/local/bin',
        '/usr/bin',
        '/bin',
    ]),
  }

  cmake_cmd = [
    "cmake", "..",
    "-DCMAKE_TOOLCHAIN_FILE=/src/Toolchain-mingw32.cmake",
    "-DCMAKE_BUILD_TYPE=" + ("Debug" if is_debug else "Release"),
    "-DENABLE_WIN32_CONSOLE=" + ("ON" if is_debug else "OFF"),
    "-DQT_HEADERS_DIR=/target/include",
    "-DQT_LIBRARY_DIR=/target/bin",
    "-DPROTOBUF_PROTOC_EXECUTABLE=/target/bin/protoc",
  ]

  executable_files = [
    "clementine.exe",
    "clementine-tagreader.exe",
    "clementine-spotifyblob.exe",
  ]

  strip_command = 'i686-w64-mingw32-strip'

  if is_portable:
    nsi_filename = 'clementine-portable.nsi'
    output_glob = 'Clementine-PortableSetup*.exe'
    upload_dest = 'portable'
  else:
    nsi_filename = 'clementine.nsi'
    output_glob = 'ClementineSetup*.exe'
    upload_dest = ('debug' if is_debug else 'release')

  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Clementine")))
  f.addStep(shell.ShellCommand(
      name="cmake", workdir="source/bin", env=env, haltOnFailure=True,
      command=cmake_cmd))
  f.addStep(shell.ShellCommand(
      name="link dependencies", workdir="source/dist/windows",
      haltOnFailure=True, command="ln -svf /src/windows/clementine-deps/* ."))
  f.addStep(shell.ShellCommand(
      name="link output", workdir="source/dist/windows", haltOnFailure=True,
      command=["ln", "-svf"] + ["../../bin/" + x for x in executable_files] + ["."]))
  f.addStep(shell.Compile(
      command=["make", "-j4"], workdir="source/bin", haltOnFailure=True))
  f.addStep(shell.ShellCommand(
      name="strip", workdir="source/bin", haltOnFailure=True, env=env,
      command=[strip_command] + executable_files))
  f.addStep(shell.ShellCommand(
      name="makensis", command=["makensis", nsi_filename],
      workdir="source/dist/windows", haltOnFailure=True))
  f.addStep(OutputFinder(pattern="dist/windows/" + output_glob))
  f.addStep(UploadPackage('win32/' + upload_dest))
  return f


def MakeFedoraBuilder(distro, unused_is_64_bit):
  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Clementine")))
  f.addStep(shell.ShellCommand(name="clean", workdir="source/bin",
      command="find ~/rpmbuild/ -type f -delete"))
  f.addStep(shell.ShellCommand(name="cmake", workdir="source/bin", haltOnFailure=True,
      command=["cmake", ".."]))
  f.addStep(shell.ShellCommand(name="maketarball", workdir="source/bin", haltOnFailure=True,
      command=["../dist/maketarball.sh"]))
  f.addStep(shell.ShellCommand(name="movetarball", workdir="source/bin", haltOnFailure=True,
      command="mv clementine-*.tar.xz ~/rpmbuild/SOURCES"))
  f.addStep(shell.Compile(name="rpmbuild", workdir="source/bin", haltOnFailure=True,
      command=["rpmbuild", "-ba", "../dist/clementine.spec"]))
  f.addStep(OutputFinder(pattern="~/rpmbuild/RPMS/*/clementine-*.rpm"))
  f.addStep(UploadPackage('fedora-' + distro))
  return f


def MakeSpotifyBlobBuilder():
  cmake_cmd = [
    "cmake", "..",
    "-DCMAKE_INSTALL_PREFIX=source/bin/installprefix",
  ]

  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Clementine")))
  f.addStep(shell.ShellCommand(name="cmake", workdir="source/bin", haltOnFailure=True,
      command=cmake_cmd))
  f.addStep(shell.Compile(workdir="source/bin", haltOnFailure=True,
      command=["make", "clementine-spotifyblob", "-j4"]))
  f.addStep(shell.ShellCommand(name="install", workdir="source/bin/ext/clementine-spotifyblob",
      haltOnFailure=True, command=["make", "install"]))
  f.addStep(shell.ShellCommand(name="strip", workdir="source/bin", haltOnFailure=True,
      command="strip spotify/version*/blob"))
  f.addStep(OutputFinder(pattern="bin/spotify/version*-*bit"))
  f.addStep(shell.SetProperty(command=["echo", SPOTIFYBASE], property="spotifybase"))
  f.addStep(master.MasterShellCommand(name="verify", command=util.Interpolate("""
    openssl dgst -sha1 -verify %(prop:spotifybase)s/clementine-spotify-public.pem \
      -signature %(prop:spotifybase)s/%(prop:output-filename)s/blob.sha1 \
      %(prop:spotifybase)s/%(prop:output-filename)s/blob
  """)))
  return f


def MakeMacBuilder():
  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Clementine")))
  f.addStep(shell.ShellCommand(
      name="cmake",
      workdir="source/bin",
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
        "-DCMAKE_LIBRARY_PATH=/target/lib",
        "-DAPPLE_DEVELOPER_ID='Developer ID Application: John Maguire (CZ8XD8GTGZ)'",
      ],
      haltOnFailure=True,
  ))
  f.addStep(shell.Compile(command=["make"], workdir="source/bin", haltOnFailure=True))
  f.addStep(shell.ShellCommand(name="install", command=["make", "install"], haltOnFailure=True, workdir="source/bin"))
  f.addStep(shell.ShellCommand(name="sign", command=["make", "sign"], haltOnFailure=True, workdir="source/bin"))
  f.addStep(shell.ShellCommand(name="dmg", command=["make", "dmg"], haltOnFailure=True, workdir="source/bin"))
  f.addStep(OutputFinder(pattern="bin/clementine-*.dmg"))
  f.addStep(UploadPackage('mac'))
  return f


def MakeMacDepsBuilder():
  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Dependencies")))
  f.addStep(shell.ShellCommand(name="clean", workdir="/src/macosx", command=["make", "clean"]))
  f.addStep(shell.ShellCommand(name="compile", workdir="/src/macosx", command=["make"]))
  return f


def _AddTxSetup(f, resource, source_file, pattern, pot=True):
  set_args = [
      "tx", "set", "--auto-local", "-r", resource, pattern,
      "--source-lang", "en", "--execute"]

  if pot:
    set_args += ["--source-file", source_file]

  f.addStep(shell.ShellCommand(name="transifexrc", haltOnFailure=True,
      command=["cp", "/config/transifexrc", "/home/buildbot/.transifexrc"]))
  f.addStep(shell.ShellCommand(name="clean", workdir="source",
      command=["rm", "-rf", ".tx"]))
  f.addStep(shell.ShellCommand(name="tx_init", workdir="source", haltOnFailure=True,
      command=["tx", "init", "--host=https://www.transifex.com"]))
  f.addStep(shell.ShellCommand(name="tx_set",  workdir="source", haltOnFailure=True,
      command=set_args))


def _AddTxSetupForRepo(f, repo, pot=True):
  if repo == "Clementine":
    _AddTxSetup(f, "clementine.clementineplayer",
        "src/translations/translations.pot",
        "src/translations/<lang>.po", pot)
  elif repo == "Website":
    _AddTxSetup(f, "clementine.website",
        "www.clementine-player.org/locale/django.pot",
        "www.clementine-player.org/locale/<lang>.po")
  elif repo == "Android-Remote":
    _AddTxSetup(f, "clementine-remote.clementine-remote",
        "app/src/main/res/values/strings.xml",
        "app/src/main/res/values-<lang>/strings.xml")
  else:
    raise ValueError(repo)


def _AddGithubSetup(f):
  f.addStep(shell.ShellCommand(name="ssh_config_cp", haltOnFailure=True,
      command=["cp", "/config/ssh-config", "/home/buildbot/.ssh/config"]))
  f.addStep(shell.ShellCommand(name="git_config_email", haltOnFailure=True,
      command=["git", "config", "--global", "user.email", "buildbot@clementine-player.org"]))
  f.addStep(shell.ShellCommand(name="git_config_username", haltOnFailure=True,
      command=["git", "config", "--global", "user.name", "Clementine Buildbot"]))


def _MakeTransifexPoPullBuilder(repo, po_glob):
  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs(repo)))
  _AddTxSetupForRepo(f, repo, pot=False)
  _AddGithubSetup(f)
  f.addStep(shell.ShellCommand(name="tx_pull", workdir="source", haltOnFailure=True,
      command=["tx", "pull", "-a", "--force"]))

  # Dialects must have a '-r' prepended instead of '_'
  if repo == "Android-Remote":
    f.addStep(shell.ShellCommand(name="remove_res", workdir="build", haltOnFailure=True,
        command="rm -rf app/src/main/res/values-??-r*"))
    f.addStep(shell.ShellCommand(name="rename_res", workdir="build", haltOnFailure=True,
        command="rename 's/_/-r/g' app/src/main/res/values-*"))

  f.addStep(shell.ShellCommand(name="git_add", workdir="source", haltOnFailure=True,
      command="git add --verbose " + po_glob))
  f.addStep(shell.ShellCommand(name="git_commit", workdir="source", haltOnFailure=True,
      command=["git",
               "commit",
               "--author=Clementine Buildbot <buildbot@clementine-player.org>",
               "--message=Automatic merge of translations from Transifex "
               "(https://www.transifex.com/projects/p/clementine/resource/clementineplayer)"]))
  f.addStep(shell.ShellCommand(name="git_push", workdir="source", haltOnFailure=True,
      command=["git",
               "push",
               "github-%s" % repo,
               "master",
               "--verbose"]))
  return f


def MakeTransifexPoPullBuilder():
  return _MakeTransifexPoPullBuilder("Clementine", "src/translations/*.po")


def MakeWebsiteTransifexPoPullBuilder():
  return _MakeTransifexPoPullBuilder(
      "Website", "www.clementine-player.org/locale/*.po")

def MakeAndroidTransifexPoPullBuilder():
  return _MakeTransifexPoPullBuilder(
      "Android-Remote", "app/src/main/res/values-*")

def MakeTransifexPotPushBuilder():
  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Clementine")))
  f.addStep(shell.ShellCommand(name="cmake", haltOnFailure=True,
      workdir="source/bin", command=["cmake", ".."]))
  f.addStep(shell.Compile(haltOnFailure=True, workdir="source/bin",
      command=["make", "-j4"]))
  _AddTxSetupForRepo(f, "Clementine")
  f.addStep(shell.ShellCommand(name="tx_push", workdir="source",
      haltOnFailure=True, command=["tx", "push", "-s"]))
  return f


def MakeWebsiteTransifexPotPushBuilder():
  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Website")))
  _AddTxSetupForRepo(f, "Website")
  f.addStep(shell.ShellCommand(name="tx_push", workdir="source", haltOnFailure=True,
      command=["tx", "push", "-s"]))
  return f


def MakeAndroidRemoteBuilder():
  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Android-Remote")))

  env = {
    'ANDROID_HOME': '/android-sdk-linux',
  }

  # Change path to properties file here
  sed_cmd = [
    'sed', '-i', '-e', 's:key.properties:/config/android-remote-properties.txt:g',
    'app/build.gradle']

  f.addStep(shell.ShellCommand(name="sed", command=sed_cmd, haltOnFailure=True,
      workdir='source'))
  f.addStep(shell.ShellCommand(name="compile", haltOnFailure=True,
      workdir='source', env=env, command=["./gradlew", "assembleRelease"]))
  f.addStep(OutputFinder(pattern="app/build/outputs/apk/ClementineRemote-release-*.apk"))
  f.addStep(UploadPackage("android"))
  return f


def MakeSourceBuilder():
  git_args = GitArgs("Clementine")
  git_args['mode'] = 'full'
  git_args['method'] = 'fresh'

  cmake_cmd = [
      'cmake', '..',
  ]

  f = factory.BuildFactory()
  f.addStep(git.Git(**git_args))
  f.addStep(shell.ShellCommand(name="cmake", command=cmake_cmd, haltOnFailure=True, workdir="source/bin"))
  f.addStep(shell.ShellCommand(command=["./maketarball.sh"], haltOnFailure=True, workdir="source/dist"))
  f.addStep(OutputFinder(pattern="dist/clementine-*.tar.xz"))
  f.addStep(UploadPackage('source'))
  return f
