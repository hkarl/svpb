#!/bin/bash 

python manage.py dumpdata --format=yaml arbeitsplan auth  > arbeitsplan/fixtures/initial_data.yaml 
rm svpb.sq 
python manage.py syncdb 

