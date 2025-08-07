#!/bin/bash

path="$(readlink -f ${BASH_SOURCE[0]})"
path="$(dirname ${path})"
root_folder="$(dirname ${path})"

cd ${root_folder}

# clean up
docker stop wss_chat || true
docker rm wss_chat || true
docker image rm tinyorb/wss_chat:3.0 || true

# publish image
docker image build -t tinyorb/wss_chat:3.0 .

HOST_APP_PORT=10008

# This is for publishing
#HOST_APP_DOMAIN=ubiquitous.tinyorb.org

# This is only for local testing
HOST_APP_DOMAIN=192.168.106.197

# if it is SSL and PROTOCOL WSS
SSL=true


# sudo docker run -d --name=wss_chat -p <host_port>:<docker_app_port>/tcp --cap-add=NET_RAW --cap-add=NET_ADMIN tinyorb/wss_chat
 sudo docker run -d --name=wss_chat -e WSS_PORT=${HOST_APP_PORT} -e WSS_HOST=${HOST_APP_DOMAIN} -e SSL=${SSL} \
  -p ${HOST_APP_PORT}:8000/tcp --cap-add=NET_RAW --cap-add=NET_ADMIN tinyorb/wss_chat:3.0

if [[ "${SSL}" == "true" ]]; then

  # sudo docker run -d --name=nw_mon_test -p 90:8991 tinyorb/python3:nw_monitor
  echo "Navigate older https://${HOST_APP_DOMAIN}:${HOST_APP_PORT}/ui"
  echo "Navigate newer https://${HOST_APP_DOMAIN}:${HOST_APP_PORT}/ui_v2"

else
  echo "Navigate older http://${HOST_APP_DOMAIN}:${HOST_APP_PORT}/ui"
  echo "Navigate newer http://${HOST_APP_DOMAIN}:${HOST_APP_PORT}/ui_v2"
fi