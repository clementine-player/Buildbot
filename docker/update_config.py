#!/usr/bin/env python

import difflib
import json
import os
import random
import string
import sys

CONFIG = json.load(open('config/config.json'))


def Add(decking, name):
  decking['images']['clementine/' + name] = './' + name
  decking['containers'][name] = {
    'image':        'clementine/' + name,
    'dependencies': ['master:master'],
    'mount':        ['./config:/config'],
    'mount-from':   ['volumes'],
  }
  decking['clusters']['main'].append(name)


def CreatePassword():
  return ''.join(
      random.choice(string.ascii_letters + string.digits)
      for _ in range(16))


def WriteDeckingJson():
  decking = {
    'images': {
      'clementine/volumes':     './volumes',
      'clementine/master':      './master',
      'clementine/slave-mingw': './slave-mingw',
    },
    'containers': {
      'volumes': {
        'image': 'clementine/volumes',
        'data': True,
      },
      'master': {
        'image':      'clementine/master',
        'port':       ['8010:8010'],
        'mount':      [
          './config:/config',
          '/var/www/clementine-player.org:/var/www/clementine-player.org'
        ],
        'mount-from': ['volumes'],
      },
      'slave-mingw': {
        'image':        'clementine/slave-mingw',
        'dependencies': ['master:master'],
        'mount':        ['./config:/config'],
        'mount-from':   ['volumes'],
      },
    },
    'clusters': {
      'main': [
        'master',
        'slave-mingw',
      ],
    },
  }

  for distro, versions in CONFIG['linux'].iteritems():
    for version in versions:
      for bits in [64, 32]:
        Add(decking, 'slave-%s-%s-%d' % (distro, version, bits))

  for slave in CONFIG['special_slaves']:
    Add(decking, 'slave-' + slave)

  with open('decking.json', 'w') as fh:
    json.dump(decking, fh, indent=2, sort_keys=True)
  print 'Wrote decking.json'


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
  WriteDeckingJson()
  WritePasswords()


if __name__ == '__main__':
  main()
