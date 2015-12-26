#!/bin/bash

# load testdata from a fixtures directory
# take care to move aside the current data base

mv svpb.sq old.sq
yes no | python manage.py syncdb  
python manage.py loaddata $1/user.json
python manage.py loaddata $1/groups.json
python manage.py loaddata $1/arbeitsplan.json
python manage.py loaddata $1/po.json


