rm svpb.sq 
scp mein.svpb.de:svpb/arbeitsplan/fixtures/*json backup/
python manage.py migrate 
python manage.py loaddata backup/*.json 
