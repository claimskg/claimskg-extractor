#!/bin/bash

DOCKER_ID=$( docker ps -aqf "name=claimskg-extractor")

EXPORTER_COMMMAND="python3 /app/Exporter.py --website=afpfactcheck --maxclaims=5"

docker exec $DOCKER_ID bash -c "$EXPORTER_COMMMAND"
