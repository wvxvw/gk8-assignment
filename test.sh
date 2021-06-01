#!/bin/sh

# Run with: sudo -E env PATH=$PATH ./test.sh 

set -ex

NODES=

for c in $(docker ps --filter "label=role=worker" --format "{{.ID}}") ; do
    IP=$(docker inspect \
                --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
                $c)
    NODES="--node $IP $NODES"
done

python \
    -m gk8_scrap \
    --url 'https://www.blockchain.com/explorer?utm_campaign=dcomnav_explorer' \
    --output coinbase.csv \
    $NODES
