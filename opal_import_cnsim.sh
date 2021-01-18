#!/bin/bash

# wait for opal to be ready

is_up() {
  nc -z -w 5 opal 8080
  if [ $? -ne 0 ]; then
    sleep 1
    is_up
  fi
}

is_up
# slight additional delay
sleep 20

/usr/bin/opal project --verbose --opal http://opal:8080 -u administrator -p 'password' --add --name CNSIM --database mongodb

ls /datashield_loadtest

/usr/bin/opal file --opal http://opal:8080 -u administrator -p 'password' --upload /datashield_loadtest/CNSIM.zip /home/administrator

/usr/bin/opal import-xml --opal http://opal:8080 -u administrator -p 'password' --path /home/administrator/CNSIM.zip --destination CNSIM

