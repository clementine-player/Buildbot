# -*- python -*-
# ex: set syntax=python:

import os

from buildbot import buildslave
from buildbot.changes import gitpoller
from buildbot.process import factory
from buildbot.schedulers import basic
from buildbot.schedulers import filter
from buildbot.schedulers import forcesched
from buildbot.status import html
from buildbot.status import mail
from buildbot.status.web import authz
from buildbot.steps import shell
from buildbot.steps import source

PASSWORD    = "hunter2"


def GitBaseUrl(repository):
  return "https://github.com/clementine-player/%s.git" % repository


def GitArgs(repository):
  return {
    "repourl": GitBaseUrl(repository),
    "branch": "master",
    "mode": "copy",
    "retry": (5*60, 3),
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


def MakeDebBuilder(dist, dist_type, arch):
  env = {
    "DEB_BUILD_OPTIONS": 'parallel=4',
  }

  cmake_cmd = [
    "cmake", "..",
    "-DWITH_DEBIAN=ON",
    "-DDEB_ARCH=" + arch,
    "-DDEB_DIST=" + dist,
    "-DENABLE_SPOTIFY_BLOB=OFF",
  ]
  make_cmd = ["make", "deb"]

  f = factory.BuildFactory()
  f.addStep(source.Git(**GitArgs("Clementine")))
  f.addStep(shell.ShellCommand(name="cmake", command=cmake_cmd, haltOnFailure=True, workdir="source/bin"))
  f.addStep(shell.Compile(command=make_cmd, haltOnFailure=True, workdir="source/bin", env=env))
  f.addStep(OutputFinder(pattern="bin/clementine_*.deb"))
  return f


def MakeWindowsDepsBuilder():
  f = factory.BuildFactory()
  f.addStep(source.Git(**GitArgs("Dependencies")))
  f.addStep(shell.ShellCommand(name="clean", workdir="source/windows", command=["make", "clean"]))
  f.addStep(shell.ShellCommand(name="compile", workdir="source/windows", command=["make"]))
  return f


def MakeFedoraBuilder():
  f = factory.BuildFactory()
  f.addStep(source.Git(**GitArgs("Clementine")))
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


# Basic config
c = BuildmasterConfig = {
  'projectName':  "Clementine",
  'projectURL':   "http://www.clementine-player.org/",
  'buildbotURL':  "http://buildbot.clementine-player.org/",
  'slavePortnum': 9989,
  'slaves': [
    buildslave.BuildSlave("precise-32",   PASSWORD),
    buildslave.BuildSlave("precise-64",   PASSWORD),
    buildslave.BuildSlave("trusty-32",    PASSWORD),
    buildslave.BuildSlave("trusty-64",    PASSWORD),
    buildslave.BuildSlave("utopic-32",    PASSWORD),
    buildslave.BuildSlave("utopic-64",    PASSWORD),
    buildslave.BuildSlave("fedora-20-32", PASSWORD),
    buildslave.BuildSlave("fedora-20-64", PASSWORD),
    buildslave.BuildSlave("fedora-21-32", PASSWORD),
    buildslave.BuildSlave("fedora-21-64", PASSWORD),
    buildslave.BuildSlave("mingw",        PASSWORD),
  ],
  'change_source': [
    gitpoller.GitPoller(
      project="clementine",
      repourl=GitBaseUrl("Clementine"),
      pollinterval=60*5, # seconds
      branch='master',
      workdir="gitpoller_work",
    ),
  ],
  'status': [
    html.WebStatus(
      http_port="tcp:8010",
      authz=authz.Authz(
        forceBuild=True,
        forceAllBuilds=True,
        stopBuild=True,
        stopAllBuilds=True,
        cancelPendingBuild=True,
        cancelAllPendingBuilds=True,
        stopChange=True,
      ),
    ),
    mail.MailNotifier(
      fromaddr="buildmaster@zaphod.purplehatstands.com",
      lookup="gmail.com",
      mode="failing",
    ),
  ],
}

change_filter = filter.ChangeFilter(project="clementine", branch=u"master")

normal_scheduler = basic.SingleBranchScheduler(
  name="deb",
  change_filter=change_filter,
  treeStableTimer=2*60,
  builderNames=[
    "Deb Trusty 64-bit",
    "Deb Precise 64-bit",
    "Deb Utopic 64-bit",
    "Deb Trusty 32-bit",
    "Deb Precise 32-bit",
    "Deb Utopic 32-bit",
  ],
)
force_scheduler = forcesched.ForceScheduler(
  name="force",
  reason=forcesched.FixedParameter(name="reason", default="force build"),
  branch=forcesched.StringParameter(name="branch", default="master"),
  revision=forcesched.FixedParameter(name="revision", default=""),
  repository=forcesched.FixedParameter(name="repository", default=""),
  project=forcesched.FixedParameter(name="project", default=""),
  properties=[],
  builderNames=[
    "Deb Trusty 64-bit",
    "Deb Precise 64-bit",
    "Deb Utopic 64-bit",
    "Deb Trusty 32-bit",
    "Deb Precise 32-bit",
    "Deb Utopic 32-bit",
    "RPM Fedora 20 32-bit",
    "RPM Fedora 20 64-bit",
    "RPM Fedora 21 32-bit",
    "RPM Fedora 21 64-bit",
    "Windows Dependencies",
  ],
)

c['schedulers'] = [
  normal_scheduler,
  force_scheduler,
]

c['builders'] = [
  {
    'name':      'Deb Precise 64-bit',
    'builddir':  'deb-precise-64',
    'slavename': 'precise-64',
    'factory':   MakeDebBuilder('precise', 'ubuntu', 'amd64'),
  },
  {
    'name':      'Deb Trusty 64-bit',
    'builddir':  'deb-trusty-64',
    'slavename': 'trusty-64',
    'factory':   MakeDebBuilder('trusty', 'ubuntu', 'amd64'),
  },
  {
    'name':      'Deb Utopic 64-bit',
    'builddir':  'deb-utopic-64',
    'slavename': 'utopic-64',
    'factory':   MakeDebBuilder('utopic', 'ubuntu', 'amd64'),
  },
  {
    'name':      'Deb Precise 32-bit',
    'builddir':  'deb-precise-32',
    'slavename': 'precise-32',
    'factory':   MakeDebBuilder('precise', 'ubuntu', 'i386'),
  },
  {
    'name':      'Deb Trusty 32-bit',
    'builddir':  'deb-trusty-32',
    'slavename': 'trusty-32',
    'factory':   MakeDebBuilder('trusty', 'ubuntu', 'i386'),
  },
  {
    'name':      'Deb Utopic 32-bit',
    'builddir':  'deb-utopic-32',
    'slavename': 'utopic-32',
    'factory':   MakeDebBuilder('utopic', 'ubuntu', 'i386'),
  },
  {
    'name':      'RPM Fedora 20 32-bit',
    'builddir':  'rpm-fedora-20-32',
    'slavename': 'fedora-20-32',
    'factory':   MakeFedoraBuilder(),
  },
  {
    'name':      'RPM Fedora 20 64-bit',
    'builddir':  'rpm-fedora-20-64',
    'slavename': 'fedora-20-64',
    'factory':   MakeFedoraBuilder(),
  },
  {
    'name':      'RPM Fedora 21 32-bit',
    'builddir':  'rpm-fedora-21-32',
    'slavename': 'fedora-21-32',
    'factory':   MakeFedoraBuilder(),
  },
  {
    'name':      'RPM Fedora 21 64-bit',
    'builddir':  'rpm-fedora-21-64',
    'slavename': 'fedora-21-64',
    'factory':   MakeFedoraBuilder(),
  },
  {
    'name':      'Windows Dependencies',
    'builddir':  'windows-dependencies',
    'slavename': 'mingw',
    'factory':   MakeWindowsDepsBuilder(),
  },
]
