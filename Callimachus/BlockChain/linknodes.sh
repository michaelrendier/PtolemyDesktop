#!/bin/bash

port=$1

if [ -z "$port" ] # if port isn't assigned
then
    echo Need to specify port number
    exit 1
fi

FILES=(Block.py Chain.py Config.py Mine.py Node.py Sync.py Genesis.py Utils.py)

mkdir JackCoin$port

for file in "${FILES[@]}"
do
    echo Syncing $file
    ln JackCoin/$file JackCoin$port/$file
done

echo Synced new JackCoin folder for port $port

exit 1
