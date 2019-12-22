#!/usr/bin/env bash
rm svpb.sq
rm testdata/*
python manage.py migrate
cp ~/Dropbox/svpb/svpbbackup.tgz.cpt testdata
cd testdata
echo uRohX5aeyei4Xoov | ccrypt -d -k - svpbbackup.tgz.cpt
tar xf svpbbackup.tgz
cd .. 

python manage.py  loaddata testdata/groups.json
python manage.py  loaddata testdata/user.json
python manage.py  loaddata testdata/arbeitsplan.json
python manage.py  loaddata testdata/post_office.json
