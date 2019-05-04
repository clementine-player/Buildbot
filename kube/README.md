### Kubernetes Setup for Clementine Buildbot

```kubectl apply -f . -R```

# Cluster Creation

```
kubeadm init --pod-network-cidr=192.168.0.0/16
kubectl apply -f https://docs.projectcalico.org/v3.3/getting-started/kubernetes/installation/hosted/rbac-kdd.yaml
kubectl apply -f https://docs.projectcalico.org/v3.3/getting-started/kubernetes/installation/hosted/kubernetes-datastore/calico-networking/1.7/calico.yaml
kubectl taint nodes --all node-role.kubernetes.io/master-
kubectl create secret generic mac-ssh-password --from-file mac-ssh-password
kubectl create secret generic slave-passwords --from-file passwords.json --from-file passwords-external.json
kubectl apply -f . -R
```

# Accessing Kubernetes Cluster

```rsync /etc/kubernetes/admin.conf ~/.kube/config```

# Accessing Kubernetes Dashboard

1. Create a user for yourself in `dash/users.yaml`
1. Print the token with:

    ```
    kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep admin-user | awk '{print $1}')`
    ```

1. Run `kubectl proxy` on your machine.
1. [Open the Dashboard](http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/)
1. Login with the token from before.
