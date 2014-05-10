python manage.py  dumpdata auth.User --format yaml > arbeitsplan/fixtures/user.yaml
python manage.py  dumpdata arbeitsplan --format yaml > arbeitsplan/fixtures/arbeitsplan.yaml
python manage.py  dumpdata auth.Group  --format yaml > arbeitsplan/fixtures/groups.yaml
cd arbeitsplan/fixtures 
cat user.yaml arbeitsplan.yaml groups.yaml > initial_data.yaml 
