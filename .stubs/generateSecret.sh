#!/bin/bash

# Generate a dummy secret.yaml file
grep -r -h -o "\!secret [a-zA-Z\-\_][a-zA-Z\-\_]*" ../ | sed -E 's/\!secret ([a-zA-Z\-\_]*)/\1: XXXXXXXXX/g' | sort | uniq -u > secrets.yaml

# Only copy to correct dir if we aren't overriding it!
if [ ! -f ../secrets.yaml ]; then
    cp secrets.yaml ../
else
    echo "Not going to overide actual secrets.yaml!"
fi
