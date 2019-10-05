#!/bin/bash

# url = https://home-assistant.com
# num|port = 0
# ip = 1.1.1.1
# else = X

# Generate a dummy secret.yaml file
grep -r -h -o "\!secret [a-zA-Z\-\_][a-zA-Z\-\_]*" ../ | sed -E 's/\!secret ([a-zA-Z\-\_]*)/\1: X/g' | sort | uniq > secrets.yaml

sed -E -i 's/(.*)_url: X/\1_url: https\/\/\:home\-assistant\.com/g' secrets.yaml

sed -E -i 's/(.*)_(num|port): X/\1_\2: 0/g' secrets.yaml

sed -E -i 's/(.*)_ip: X/\1_ip: 1.1.1.1/g' secrets.yaml

# Only copy to correct dir if we aren't overriding it!
if [ ! -f ../secrets.yaml ]; then
    cp secrets.yaml ../
else
    echo "Not going to overide actual secrets.yaml!"
fi
