#!/bin/bash
MyUSER="root"
MyPass="qwertyuiop"
MyHOST="localhost"

MYSQL="$(which mysql)"
MYSQLDUMP="$(which mysqldump)"
CHOWN="$(which chown)"
CHMOD="$(which chmod)"
GZIP="$(which gzip)"
CURUSER="$(which whoami)"

#日志文件路径
LOGFILE=/tmp/change_mysql_engine.log

NOW="$(date +"%d-%m-%Y %H:%M:%S")"
#要操作的数据库
DBS="shoptmp"
DTS=""
#忽略的表列表
IGGY="*_tmp"
#包含的表列表
INGY="shop_trades_*"

DTS="$($MYSQL -u $MyUSER -h $MyHOST $DBS -Bse 'show tables')"

echo "======= $NOW change $DBS to innodb engine start  ======" >> $LOGFILE

for dt in $DTS
do
	skipdb=-1
	incldb=1
	if [ "$IGGY" != "" ];
	then
		for i in $IGGY
		do
			[[ "$dt" == $i ]] && skipdb=1 || :
		done
	fi
	
	if [ "$INGY" != "" ];
	then
		for i in $INGY
		do
			[[ "$dt" == $i ]] && incldb=-1 || :
		done
	fi
	
	echo "check: ${dt}, ${skipdb} , ${incldb}" >> $LOGFILE
	
	if [ "$skipdb" == "-1" ] && [ "$incldb" == "-1" ];
	then
			
		#复制数据
		#$MYSQL -u $MyUSER -h $MyHOST  -Bse "INSERT INTO ${DBS}.${dt} SELECT * FROM shopmgr.${dt}" 
		
		#echo "======= $NOW $dt changed to innodb success  ======" >> $LOGFILE
	fi
done
		
		