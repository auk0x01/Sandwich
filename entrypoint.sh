#!/bin/sh

# Setting environment variables
export ADMIN_PASSWORD=$(cat /dev/urandom | tr -cd "a-f0-9" | head -c 40) 
export SECRET_KEY=$(cat /dev/urandom | tr -cd "a-f0-9" | head -c 40)
export CLOCK_SEQUENCE=$(cat /dev/urandom | tr -cd "0-9" | head -c 40)

# Setting up database
python3 database_setup.py

# Starting the application
python3 app.py