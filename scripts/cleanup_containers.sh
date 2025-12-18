#!/bin/bash
ids=$(docker ps -a -q --filter name=somaAgent01)
if [ -n "$ids" ]; then
    echo "Removing: $ids"
    docker rm -f $ids
else
    echo "No containers found."
fi
