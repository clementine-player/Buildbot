from golang:1.9 as build

WORKDIR /build

ENV GOPATH /go
RUN go get github.com/clementine-player/codesigner/codesigner-server
RUN GOOS=darwin go build github.com/clementine-player/codesigner/codesigner-server

FROM alpine:3.5
RUN apk add --no-cache rsync openssh-client sshpass
COPY --from=build /build/codesigner-server /go/bin/codesigner-server

ADD bootstrap.sh /bootstrap.sh
RUN chmod 555 /bootstrap.sh

CMD ["/bootstrap.sh"]
