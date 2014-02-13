#!/bin/bash

export PATH=/Users/buildbot/clang-3.4/bin:$PATH
export CC=clang
export CXX=clang++

set -e

read -s -p "Enter buildbot keychain password: " password

# Unlock keychain
security unlock-keychain -p "$password" buildbot.keychain

buildslave start
