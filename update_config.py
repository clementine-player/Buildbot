#!/usr/bin/env python

import difflib
import json
import os
import random
import string
import sys
import yaml

CONFIG = json.load(open('config/config.json'))


def Add(compose, name):
  compose[name] = {
    'build': name,
    'links': ['master'],
    'volumes': ['./config:/config'],
    'volumes_from': ['volumes'],
  }


def CreatePassword():
  return ''.join(
      random.choice(string.ascii_letters + string.digits)
      for _ in range(16))


def WriteComposeYaml():
  compose = {
    'master': {
      'build': 'master',
      'ports': [
        '8010:8010',
        '9989:9989',
      ],
      'volumes': [
        './config:/config',
        '/var/www/clementine-player.org',
      ],
      'volumes_from': ['volumes'],
    },
    'volumes': {
      'command': '/bin/true',
      'image': 'ubuntu',
      'volumes': ['/persistent-data'],
    }
  }

  for distro, versions in CONFIG['linux'].iteritems():
    for version in versions:
      for bits in [64, 32]:
        Add(compose, str('slave-%s-%s-%d' % (distro, version, bits)))

  for slave in CONFIG['special_slaves']:
    Add(compose, str('slave-' + slave))

  with open('docker-compose.yml', 'w') as fh:
    yaml.dump(compose, fh, indent=2)
  print 'Wrote docker-compose.yml'


def WritePasswords():
  slaves = []
  slaves.extend(CONFIG['special_slaves'])
  for distro, versions in CONFIG['linux'].iteritems():
    for version in versions:
      for bits in [64, 32]:
        slaves.append('%s-%s-%d' % (distro, version, bits))

  passwords = {name: CreatePassword() for name in slaves}

  with open('config/passwords.json', 'w') as fh:
    json.dump(passwords, fh, indent=2, sort_keys=True)
  print 'Wrote config/passwords.json'


def main():
  WriteComposeYaml()
  WritePasswords()


if __name__ == '__main__':
  main()
