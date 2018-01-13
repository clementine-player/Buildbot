### Kubernetes Setup for Clementine Buildbot

```kubectl apply -f . -R```

# Cluster Creation

```
kubeadm init --pod-network-cidr=192.168.0.0/16
kubectl taint nodes --all node-role.kubernetes.io/master-
kubectl create secret generic mac-ssh-password --from-file mac-ssh-password
kubectl create secret generic slave-passwords --from-file passwords.json --from-file passwords-external.json
kubectl apply -f . -R
```
