#!/usr/bin/env bash

python3 examplenode1.py 4000 42 tcp://localhost:5000 tcp://localhost:6000 > 4000.log.txt 2>&1 &
pid_1=$!

python3 examplenode1.py 5000 42 tcp://localhost:4000 tcp://localhost:6000 > 5000.log.txt 2>&1 &
pid_2=$!

python3 examplenode1.py 6000 42 tcp://localhost:4000 tcp://localhost:5000 > 6000.log.txt 2>&1 &
pid_3=$!

echo "Spawned 3 nodes with pid" $pid_1 $pid_2 $pid_3
