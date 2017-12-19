#!/bin/sh

SSHPASS="sshpass -f /secrets/mac-ssh-password"

${SSHPASS} rsync -Lv -e "ssh -p2222 -oStrictHostKeyChecking=no -oConnectTimeout=60" \
  /go/bin/codesigner-server \
  /etc/tls/tls.key \
  /etc/tls/tls.crt \
  /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  buildbot@localhost:
${SSHPASS} ssh -p2222 buildbot@localhost ./codesigner-server -cert tls.crt -key tls.key -ca ca.crt -port 5001
