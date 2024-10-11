#!/bin/bash

# Instructions to setup a virtual environment for Streamlit / Amazon Bedrock app
# Command to run: sh ./env_setup.sh

# Create a new Python3 virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip
pip install pip --upgrade

# Install required packages
pip install -r requirements.txt --upgrade

echo "Virtual Python environment '.venv' has been created and activated."
