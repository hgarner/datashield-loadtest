/usr/bin/opal project --verbose --opal http://opal:8080 -u administrator -p 'password' --add --name CNSIMTEST --database mongodb

/usr/bin/opal file --opal http://localhost:8080 -u administrator -p 'password' /datashield-loadtest_parent/CNSIM.zip /home/administrator

/usr/bin/opal import-xml --opal http://localhost:8080 -u administrator -p 'password' --path /home/administrator/CNSIM.zip --destination CNSIM

