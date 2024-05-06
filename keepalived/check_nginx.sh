#!/bin/sh

APISERVER_DEST_PORT=80
APISERVER_VIP=192.168.31.254 

errorExit() {
    echo "*** $*" 1>&2
    exit 1
}

curl --silent --max-time 2 --insecure http://localhost:${APISERVER_DEST_PORT}/ -o /dev/null || errorExit "Error GET http://localhost:${APISERVER_DEST_PORT}/"
if ip addr | grep -q ${APISERVER_VIP}; then
    curl --silent --max-time 2 --insecure http://${APISERVER_VIP}:${APISERVER_DEST_PORT}/ -o /dev/null || errorExit "Error GET http://${APISERVER_VIP}:${APISERVER_DEST_PORT}/"
fi
