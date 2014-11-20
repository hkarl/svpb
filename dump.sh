python manage.py  dumpdata auth.User --format json > arbeitsplan/fixtures/user.json
python manage.py  dumpdata arbeitsplan --format json > arbeitsplan/fixtures/arbeitsplan.json
python manage.py  dumpdata post_office --format json > arbeitsplan/fixtures/post_office.json
python manage.py  dumpdata auth.Group  --format json > arbeitsplan/fixtures/groups.json
cd arbeitsplan/fixtures 
tar cfz svpbbackup.tgz *json 
echo XXXX | ccrypt -f -k - svpbbackup.tgz
cp svpbbackup.tgz.cpt /home/svpb/Dropbox/svpb



# cat user.json arbeitsplan.json groups.json post_office.json > initial_data.json 
