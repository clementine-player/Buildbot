#!/bin/bash

set -e

read -s -p "Enter buildbot keychain password: " password

# Unlock keychain
security unlock-keychain -p "$password" buildbot.keychain

buildslave start
