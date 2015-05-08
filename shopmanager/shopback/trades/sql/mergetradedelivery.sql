CREATE TABLE `shop_trades_delivery` (
    `id` bigint(20) auto_increment NOT NULL PRIMARY KEY,
    `seller_id` integer,
    `trade_id` bigint NOT NULL UNIQUE,
    `trade_no` varchar(64) NOT NULL,
    `buyer_nick` varchar(64) NOT NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `delivery_time` datetime,
    `is_parent` bool NOT NULL,
    `is_sub` bool NOT NULL,
    `parent_tid` bigint NOT NULL,
    `message` varchar(126) NOT NULL,
    `status` integer NOT NULL
)ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

CREATE INDEX `shop_trades_delivery_2ef613c9` ON `shop_trades_delivery` (`seller_id`);
CREATE INDEX `shop_trades_delivery_7c3a2abd` ON `shop_trades_delivery` (`trade_no`);
CREATE INDEX `shop_trades_delivery_283c66fa` ON `shop_trades_delivery` (`delivery_time`);
CREATE INDEX `shop_trades_delivery_f6c689db` ON `shop_trades_delivery` (`parent_tid`);
