#!/bin/sh

# Run with: sudo -E env PATH=$PATH ./test.sh
# Short path to coinbase:
# https://www.blockchain.com/btc/tx/478ed0065aeab602fedba0d1d87dc6c901f7a91a2ba7a7710563cde906ea5846

set -ex

NODES=

for c in $(docker ps --filter "label=role=worker" --format "{{.ID}}") ; do
    IP=$(docker inspect \
                --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
                $c)
    NODES="--node $IP $NODES"
done

# --url 'https://www.blockchain.com/explorer?utm_campaign=dcomnav_explorer'

python \
    -m gk8_scrap \
    --transaction 478ed0065aeab602fedba0d1d87dc6c901f7a91a2ba7a7710563cde906ea5846 \
    --output coinbase.json \
    --verbosity 20 \
    $NODES
