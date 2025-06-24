#!/bin/bash

mkdir $PWD/venv

python3 -m venv ${PWD}/venv

source ${PWD}/venv/bin/activate
pip install --upgrade pip

pip install -r src/dependencies.txt

source venv/bin/activate