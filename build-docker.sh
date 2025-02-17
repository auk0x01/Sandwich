#!/bin/bash

docker rm sandwich
docker build -t sandwich .
docker run --name=sandwich -p 1337:1337 -it sandwich