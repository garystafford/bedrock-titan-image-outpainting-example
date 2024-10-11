#!/bin/bash

# Instructions to setup a virtual environment for Streamlit / Amazon Bedrock app
# Command to run: sh ./env_setup.sh

# Create a new Python3 virtual environment
python3 -m venv streamlit_bedrock

# Activate the virtual environment
source streamlit_bedrock/bin/activate

# Upgrade pip
pip install pip  -Uq

# Install required packages
# pip install boto3 botocore streamlit -Uq
pip install -r requirements.txt -Uq

echo "Virtual environment 'streamlit_bedrock' has been created and activated."