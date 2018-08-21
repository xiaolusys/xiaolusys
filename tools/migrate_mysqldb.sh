#!/bin/bash
MyUSER="xiaoludev"     # USERNAME
MyPASS="xiaolu_test123"       # PASSWORD
MyHOST="rdsvrl2p9pu6536n7d99.mysql.rds.aliyuncs.com"          # Hostname

# Linux bin paths, change this if it can not be autodetected via which command
MYSQL="$(which mysql)"
MYSQLDUMP="$(which mysqldump)"
CHOWN="$(which chown)"
CHMOD="$(which chmod)"
GZIP="$(which gzip)"

# Backup Dest directory, change this if you have someother location
DEST="/root/backup"

# Main directory where backup will be stored
MBD="$DEST/mysql"

# Get hostname
HOST="$(hostname)"

# Get data in dd-mm-yyyy format
NOW="$(date +"%d-%m-%Y-%M-%S")"

# File to store current backup file
FILE=""
# Store list of hdatabases
DBS="flashsale"

# DO NOT BACKUP these databases
IGGY="test information_schema mysql performance_schema shoptest shopyp supplychain shopmgr"

[ ! -d $MBD ] && mkdir -p $MBD || :

# Only root can access it!
$CHOWN 0.0 -R $MBD
$CHMOD 0600 $MBD

# Get all database list first
#DBS="$($MYSQL -u $MyUSER -h $MyHOST -p$MyPASS -Bse 'show databases')"
DBTS="supplychain_supply_supplier supplychain_supply_charge supplychain_supply_product supply_chain_buyer_group supplychain_product_1st supplychain_product_2nd supplychain_product_3rd supplychain_product_4th supplychain_product_5th"


for db in $DBS
do
    skipdb=-1
    if [ "$IGGY" != "" ];
    then
        for i in $IGGY
        do
            [ "$db" == "$i" ] && skipdb=1 || :
        done
    fi

    if [ "$skipdb" == "-1" ] ; then
        FILE="$MBD/$db.$HOST.$NOW.gz"
        # do all inone job in pipe,
        # connect to mysql using mysqldump for select mysql database
        # and pipe it out to gz file in backup dir :)
	for tb in $DBTS
	do
            $MYSQLDUMP -u $MyUSER -h $MyHOST -p$MyPASS $db $tb >> $FILE
	done
    fi