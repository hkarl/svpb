rm svpb.sq 
python manage.py migrate 
python manage.py loaddata backup/*.json 
