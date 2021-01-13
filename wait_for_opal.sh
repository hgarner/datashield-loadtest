#!/bin/bash

# wait for opal to be ready

echo "Waiting for Opal (opal:8080) to be ready..."

is_up() {
  nc -z -w 5 opal 8080
  if [ $? -ne 0 ]; then
    sleep 2
    is_up
  fi
}

is_up
# slight additional delay
sleep 10

echo "Opal (opal:8080) is ready..."
