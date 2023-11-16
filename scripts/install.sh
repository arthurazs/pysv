#!/bin/bash

if [ ! -d .venv ]; then
    echo "> Creating virtual environment..."
    python3.10 -m venv .venv
else
    echo "> The .venv folder already exists. Skipping virtual environment creation..."
fi

echo "> Activating virtual environment..."
. .venv/bin/activate

echo "> Upgrading pip..."
pip install --upgrade pip

echo "> Installing dependencies [extras: $1 $2]..."
if [ -z $1 ]; then
    pip install .
elif [ -z $2 ]; then
    pip install .[$1]
else
    pip install .[$1,$2]
fi

