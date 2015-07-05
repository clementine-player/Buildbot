#!/bin/sh
set -e -x

mount binfmt_misc -t binfmt_misc /proc/sys/fs/binfmt_misc
echo ':DOSWin:M::MZ::/usr/bin/wine:' > /proc/sys/fs/binfmt_misc/register