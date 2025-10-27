#!/bin/bash

VENV_DIR=$PWD/venv

if [ -d $VENV_DIR ]; then
    echo "Python virtual environement 'venv' already exists. Setup terminated."
    exit 1
fi

python3 -m venv $VENV_DIR

source $VENV_DIR/bin/activate

pip install --upgrade pip
pip install -r src/dependencies.txt