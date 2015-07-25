from buildbot.steps import shell
from buildbot.process import factory
from buildbot.steps.source import git

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


class OutputFinder(shell.ShellCommand):
  def __init__(self, pattern=None, **kwargs):
    if pattern is None:
      shell.ShellCommand.__init__(self, **kwargs)
    else:
      shell.ShellCommand.__init__(self,
        name="get output filename",
        command=["sh", "-c", "basename `ls -d " + pattern + "|head -n 1`"],
        workdir="source",
        **kwargs
      )

  def commandComplete(self, cmd):
    filename = self.getLog('stdio').readlines()[0].strip()
    self.setProperty("output-filename", filename)


def MakeDebBuilder(distro, is_64_bit):
  arch = 'amd64' if is_64_bit else 'i386'

  env = {
    "DEB_BUILD_OPTIONS": 'parallel=4',
  }

  cmake_cmd = [
    "cmake", "..",
    "-DWITH_DEBIAN=ON",
    "-DDEB_ARCH=" + arch,
    "-DDEB_DIST=" + distro,
    "-DENABLE_SPOTIFY_BLOB=OFF",
  ]
  make_cmd = ["make", "deb"]

  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Clementine")))
  f.addStep(shell.ShellCommand(name="cmake", command=cmake_cmd, haltOnFailure=True, workdir="source/bin"))
  f.addStep(shell.Compile(command=make_cmd, haltOnFailure=True, workdir="source/bin", env=env))
  f.addStep(OutputFinder(pattern="bin/clementine_*.deb"))
  return f


def MakePPABuilder(distro, ppa):
  git_args = GitArgs("Clementine")
  git_args['mode'] = 'full'

  cmake_cmd = [
    "cmake", "..",
    "-DWITH_DEBIAN=ON",
    "-DDEB_DIST=" + distro,
  ]
  buildpackage_cmd = ["dpkg-buildpackage", "-S", "-kF6ABD82E"]
  dput_cmd = "dput --simulate %s *_source.changes" % ppa

  f = factory.BuildFactory()
  f.addStep(git.Git(**git_args))
  f.addStep(shell.ShellCommand(name="cmake", command=cmake_cmd, haltOnFailure=True, workdir="source/bin"))
  f.addStep(shell.ShellCommand(name="maketarball", command=["dist/maketarball.sh"], haltOnFailure=True, workdir="source"))
  f.addStep(shell.ShellCommand(name="buildpackage", command=buildpackage_cmd, haltOnFailure=True, workdir="source"))
  f.addStep(shell.ShellCommand(name="dput", command=dput_cmd, haltOnFailure=True, workdir="."))
  return f


def MakeWindowsDepsBuilder():
  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Dependencies")))
  f.addStep(shell.ShellCommand(name="clean", workdir="source/windows", command=["make", "clean"]))
  f.addStep(shell.ShellCommand(name="compile", workdir="source/windows", command=["make"]))
  return f


def MakeWindowsBuilder(is_debug):
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
    "-DCMAKE_BUILD_TYPE=Release",
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
      command=["make", "-j8"], workdir="source/bin", haltOnFailure=True))
  f.addStep(shell.ShellCommand(
      name="strip", workdir="source/bin", haltOnFailure=True, env=env,
      command=[strip_command] + executable_files))
  f.addStep(shell.ShellCommand(
      name="makensis", command=["makensis", "clementine.nsi"],
      workdir="source/dist/windows", haltOnFailure=True))
  f.addStep(OutputFinder(pattern="dist/windows/ClementineSetup*.exe"))

  return f


def MakeFedoraBuilder(unused_distro, unused_is_64_bit):
  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("Clementine")))
  f.addStep(shell.ShellCommand(name="clean", workdir="source/bin", haltOnFailure=True,
      command="find ~/rpmbuild/ -type f -delete"))
  f.addStep(shell.ShellCommand(name="cmake", workdir="source/bin", haltOnFailure=True,
      command=["cmake", ".."]))
  f.addStep(shell.ShellCommand(name="maketarball", workdir="source/bin", haltOnFailure=True,
      command=["../dist/maketarball.sh"]))
  f.addStep(shell.ShellCommand(name="movetarball", workdir="source/bin", haltOnFailure=True,
      command="mv clementine-*.tar.gz ~/rpmbuild/SOURCES"))
  f.addStep(shell.Compile(name="rpmbuild", workdir="source/bin", haltOnFailure=True,
      command=["rpmbuild", "-ba", "../dist/clementine.spec"]))
  f.addStep(OutputFinder(pattern="~/rpmbuild/RPMS/*/clementine-*.rpm"))
  return f
  