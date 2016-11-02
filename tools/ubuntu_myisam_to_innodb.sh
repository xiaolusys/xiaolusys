#!/bin/bash
MyUSER="meixqhi"
MyPass="123123"
MyHOST="192.168.0.28"


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
DBS="shopmgr"
DTS=""
#忽略的表列表
IGGY="*_tmp"
#包含的表列表
INGY="shop_purchases_*"

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
		MyOPTBS=$($MYSQL -u $MyUSER -h $MyHOST  $DBS -Bse "SHOW TABLES LIKE '${dt}_tp'")
		#如果没有查到带_tmp后缀的表名，则执行下去
		if [ -z $MyOPTBS ];
		then
			#将表重命名为[name]_tmp
			$MYSQL -u $MyUSER -h $MyHOST  $DBS -Bse "RENAME TABLE $dt TO ${dt}_tp" 
			#创建新表，并将数据导入
			$MYSQL -u $MyUSER -h $MyHOST  $DBS -Bse "CREATE TABLE $dt like ${dt}_tmp" 
			#将表的engine改为INNODB
			$MYSQL -u $MyUSER -h $MyHOST  $DBS -Bse "ALTER TABLE $dt ENGINE=INNODB" 
			#
			$MYSQL -u $MyUSER -h $MyHOST  $DBS -Bse "INSERT INTO  $dt SELECT * FROM ${dt}_tp" 
			echo "======= $NOW $dt changed to innodb success  ======" >> $LOGFILE
		else
			echo "======= $NOW $dt is already exist  ======" >> $LOGFILE
		fi
	fi
done
		
		