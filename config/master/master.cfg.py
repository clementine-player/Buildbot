# -*- python -*-
# ex: set syntax=python:

import functools
import imp
import json
import os
import pprint
import re

from buildbot import buildslave
from buildbot import locks
from buildbot.schedulers import basic
from buildbot.schedulers import filter
from buildbot.schedulers import forcesched
from buildbot.schedulers import timed
from buildbot.status import html
from buildbot.status import mail
from buildbot.status.web import authz

from clementine import builders

LINUX_FACTORIES = {
  'debian': functools.partial(builders.MakeDebBuilder, 'debian'),
  'ubuntu': functools.partial(builders.MakeDebBuilder, 'ubuntu'),
  'fedora': builders.MakeFedoraBuilder,
}
DEV_PPA = 'ppa:me-davidsansome/clementine-dev'
OFFICIAL_PPA = 'ppa:me-davidsansome/clementine'
CONFIG = json.load(open('/config/config.json'))
PASSWORDS = json.load(open('/config/passwords.json'))
PASSWORDS.update(json.load(open('/config/passwords-external.json')))


class ClementineBuildbot(object):
  def __init__(self):
    self.slaves = []
    self.builders = []
    self.auto_builder_names = []
    self.local_builder_lock = locks.MasterLock("local", maxCount=2)
    self.deps_lock = locks.SlaveLock("deps", maxCount = 1)

    # Add linux slaves and builders.
    for linux_distro, versions in CONFIG['linux'].iteritems():
      factory = LINUX_FACTORIES[linux_distro]
      for version in versions:
        self._AddBuilderAndSlave(linux_distro, version, False, factory)
        self._AddBuilderAndSlave(linux_distro, version, True, factory)

    # Add Ubuntu PPAs.
    for version in CONFIG['linux']['ubuntu']:
      self._AddBuilder(name='Ubuntu dev PPA %s' % version.title(),
                       slave='ubuntu-%s-32' % version,
                       build_factory=builders.MakePPABuilder(version, DEV_PPA))
      self._AddBuilder(name='Ubuntu official PPA %s' % version.title(),
                       slave='ubuntu-%s-32' % version,
                       build_factory=builders.MakePPABuilder(version, OFFICIAL_PPA),
                       auto=False)

    # Add special slaves.
    for name in CONFIG['special_slaves']:
      self._AddSlave(name)

    # Windows.
    self._AddBuilder(name='Windows Release',
                     slave='mingw',
                     build_factory=builders.MakeWindowsBuilder(
                         is_debug=False, is_portable=False),
                     deps_lock='counting')
    self._AddBuilder(name='Windows Debug',
                     slave='mingw',
                     build_factory=builders.MakeWindowsBuilder(
                         is_debug=True, is_portable=False),
                     deps_lock='counting')
    self._AddBuilder(name='Windows Portable',
                     slave='mingw',
                     build_factory=builders.MakeWindowsBuilder(
                         is_debug=False, is_portable=True),
                     deps_lock='counting')

    # Mac.
    self._AddBuilder(name='Mac Cross',
                     slave='mac-cross',
                     build_factory=builders.MakeMacCrossBuilder())

    # Spotify.
    self._AddBuilder(name='Spofify blob 32-bit',
                     slave='spotify-blob-32',
                     build_factory=builders.MakeSpotifyBlobBuilder())
    self._AddBuilder(name='Spofify blob 64-bit',
                     slave='spotify-blob-64',
                     build_factory=builders.MakeSpotifyBlobBuilder())

    # Transifex.
    self._AddBuilder(name='Transifex Android PO pull',
                     slave='transifex',
                     build_factory=builders.MakeAndroidTransifexPoPullBuilder(),
                     auto=False)

    # Android.
    self._AddBuilder(name='Android Remote',
                     slave='android',
                     build_factory=builders.MakeAndroidRemoteBuilder(),
                     auto=False)

    # Source.
    self._AddBuilder(name='Source',
                     slave='ubuntu-xenial-64',
                     build_factory=builders.MakeSourceBuilder())


  def _AddBuilderAndSlave(self, distro, version, is_64_bit, factory):
    bits = '64' if is_64_bit else '32'
    slave = '%s-%s-%s' % (distro, version, bits)
    self._AddBuilder(
        name='%s %s %s-bit' % (distro.title(), version.title(), bits),
        slave=slave,
        build_factory=factory(version, is_64_bit),
    )
    self._AddSlave(slave)

  def _AddBuilder(self, name, slave, build_factory,
                  auto=True,
                  local_lock=True,
                  deps_lock=None):
    locks = []
    if local_lock:
      locks.append(self.local_builder_lock.access('counting'))
    if deps_lock is not None:
      locks.append(self.deps_lock.access(deps_lock))

    self.builders.append({
        'name':      str(name),
        'builddir':  str(re.sub(r'[^a-z0-9_-]', '-', name.lower())),
        'slavename': str(slave),
        'factory':   build_factory,
        'locks':     locks,
    })

    if auto:
      self.auto_builder_names.append(name)

  def _AddSlave(self, name):
    self.slaves.append(buildslave.BuildSlave(str(name), PASSWORDS[name]))

  def Config(self):
    return {
      'projectName':  "Clementine",
      'projectURL':   "http://www.clementine-player.org/",
      'buildbotURL':  "http://buildbot.clementine-player.org/",
      'slavePortnum': 9989,
      'slaves': self.slaves,
      'builders': self.builders,
      'change_source': [
        builders.GitPoller("Android-Remote"),
        builders.GitPoller("Clementine"),
        builders.GitPoller("Dependencies"),
        builders.GitPoller("Website"),
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
      'schedulers': [
        basic.SingleBranchScheduler(
          name="automatic",
          change_filter=filter.ChangeFilter(project="clementine", branch="master"),
          treeStableTimer=2*60,
          builderNames=self.auto_builder_names,
        ),
        basic.SingleBranchScheduler(
          name="qt5",
          change_filter=filter.ChangeFilter(project="clementine", branch="qt5"),
          treeStableTimer=2*60,
          builderNames=[
            'Ubuntu Bionic 64-bit',
          ],
        ),
        basic.SingleBranchScheduler(
          name="android-remote",
          change_filter=filter.ChangeFilter(project="android-remote", branch="master"),
          treeStableTimer=2*60,
          builderNames=[
            "Android Remote",
          ],
        ),
        forcesched.ForceScheduler(
          name="force",
          reason=forcesched.FixedParameter(name="reason", default="force build"),
          branch=forcesched.StringParameter(name="branch", default="master"),
          revision=forcesched.FixedParameter(name="revision", default=""),
          repository=forcesched.FixedParameter(name="repository", default=""),
          project=forcesched.FixedParameter(name="project", default=""),
          properties=[],
          builderNames=[x['name'] for x in self.builders],
        ),
      ],
    }

BuildmasterConfig = ClementineBuildbot().Config()
pprint.pprint(BuildmasterConfig)
