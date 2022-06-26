#!/bin/bash

export PATH="/home/ec2-user/Python-3.10.4:$PATH"

source ~/.bash_profile


cd /home/ec2-user/Practica_Cloud

source ./venv/bin/activate

pip install -r requirements.txt

python /home/ec2-user/Practica_Cloud/webscrapping.py

deactivate
