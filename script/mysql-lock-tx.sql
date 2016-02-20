-- 查找被锁定的事务
-- http://blog.csdn.net/mangmang2012/article/details/9207007
select * from information_schema.innodb_trx;