#!/bin/bash

[ "$HOSTMASTER_ADDRESS" == "" -o "$POSTGRES_USER" == "" -o "$POSTGRES_SERVER" == '' ] && \
echo "Usage: set \$HOSTMASTER_ADDRESS, \$POSTGRES_SERVER and \$POSTGRES_USER variables" && exit 1
cat base_rules.sql functions.sql base_tables.sql network.sql services.sql \
vhosts.sql mailboxes.sql server_views.sql misc.sql |\
sed s/hostmaster@example.com/$HOSTMASTER_ADDRESS/g  > /tmp/createtables.sql

echo 'Importing database schema...'
psql -U $POSTGRES_USER -h $POSTGRES_SERVER services -qf /tmp/createtables.sql
[ $? -ne 0 ] && echo 'Error processsing sql' && exit 1
echo "Successfully imported"
exit 0
