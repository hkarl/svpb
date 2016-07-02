#!/bin/bash

# normal dump: 
python manage.py  dumpdata auth.User --format json > $1/user.json
python manage.py  dumpdata arbeitsplan --format json > $1/arbeitsplan.json
python manage.py  dumpdata post_office --format json > $1/po.json
python manage.py  dumpdata auth.Group  --format json > $1/groups.json

# prettty-print:
for d in $1/*.json ; do 
    echo $d
    echo $1/`basename -s .json $d`.html 
    python -m json.tool $d  | pygmentize -O full,style=emacs -l javascript  -f html -o $1/`basename -s .json $d`.html 
done

# and cycle back the previous database 
mv old.sq svpb.sq 
