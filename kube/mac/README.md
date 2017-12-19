# A Kubernetes Deployment for running the mac codesigner GRPC service

This directory contains tools for running clementine-player/codesigner as a server on a mac VM in kubernetes.

## Setup

### Add the SSH password for the mac VM to kubernetes

```kubectl create secret generic mac-ssh-password --from-file ./mac-ssh-password```

### Deploy to Kubernetes!

```kubectl apply -f slave-mac.yaml```

### Approve the Server Certificate Request

1. ```kubectl get csr```
1. Find the newest CSR from `system:serviceaccount:default:certificate-init`.
1. ```kubectl certificate approve <csr name>```

### Check things are working fine

```kubectl get pods -l app=codesigner```

```kubectl logs -l app=codesigner -c mac-sidecar```

## Rebuilding the docker image

1. ```docker build -t gcr.io/clementine-data/mac-vm .```
1. ```gcloud docker -- push gcr.io/clementine-data/mac-vm```

## Debugging

### Create a set of client certificates
1. Install Certstrap:

    ```go get github.com/square/certstrap```

1. Create a key and CSR:

    ```certstrap request-cert --common-name polyglot```
    
1. Ask Kubernetes to sign your new certificate:

    ```
    cat <<EOF | kubectl create -f -
    apiVersion: certificates.k8s.io/v1beta1
    kind: CertificateSigningRequest
    metadata:
      name: polyglot
    spec:
      groups:
      - system:authenticated
      request: $(cat out/polyglot.csr | base64 | tr -d '\n')
      usages:
      - client auth
    EOF
    ```
1. Tell Kubernetes to approve your CSR:

    ```kubectl certificate approve polyglot```
    
1. Fetch your signed certificate from Kubernetes:

    ```kubectl get csr polyglot -o jsonpath='{.status.certificate}' | base64 -d > out/polyglot.crt```

### Test the service
1. Find the service port

    ```kubectl get service/codesigner```
    
1. Extract the Kubernetes CA certificate

    ```grep certificate-authority-data <~/.kube/config | awk '{print $2}' | base64 -d > out/ca.crt```

1. Test the service with openssl

    ```openssl s_client -connect localhost:<port> -cert out/polyglot.crt -key out/polyglot.crt -CAfile out/ca.crt```
    
1. Test the service with polyglot

    ```echo "{}" | java -jar polyglot.jar --endpoint localhost:<port> --tls_client_cert_path out/polyglot.crt --tls_client_key_path out/polyglot.key --tls_ca_cert_path out/ca.crt --use_tls=true --command call --full_method codesigner.CodeSigner/SignPackage```
