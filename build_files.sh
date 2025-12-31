#!/bin/bash
echo "Building the project..."
python3.12 -m pip install -r requirements.txt
echo "Make Migration..."
python3.12 manage.py makemigrations
python3.12 manage.py migrate
echo "Collect Static..."
python3.12 manage.py collectstatic --noinput --clear
