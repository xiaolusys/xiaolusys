BEGIN;
DROP OR CREATE TABLE `flashsale_register` (
    `id` bigint(20) auto_increment NOT NULL PRIMARY KEY,
    `cus_uid` bigint,
    `vmobile` varchar(11) NOT NULL,
    `verify_code` varchar(8) NOT NULL,
    `vemail` varchar(8) NOT NULL,
    `mail_code` varchar(128) NOT NULL,
    `verify_count` integer NOT NULL,
    `submit_count` integer NOT NULL,
    `mobile_pass` bool NOT NULL,
    `mail_pass` bool NOT NULL,
    `code_time` datetime,
    `mail_time` datetime,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

DROP OR CREATE TABLE `flashsale_customer` (
    `id` bigint(20) auto_increment NOT NULL PRIMARY KEY,
    `user_id` bigint NOT NULL,
    `nick` varchar(32) NOT NULL,
    `mobile` varchar(11) NOT NULL,
    `email` varchar(32) NOT NULL,
    `phone` varchar(18) NOT NULL,
    `openid` varchar(28) NOT NULL,
    `unionid` varchar(28) NOT NULL,
    `status` integer NOT NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
ALTER TABLE `flashsale_customer` ADD CONSTRAINT `user_id_refs_id_af10b6e4` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

DROP OR CREATE TABLE `flashsale_trade` (
    `id` bigint(20) auto_increment NOT NULL PRIMARY KEY,
    `tid` varchar(40) NOT NULL UNIQUE,
    `buyer_id` bigint NOT NULL,
    `buyer_nick` varchar(64) NOT NULL,
    `channel` varchar(16) NOT NULL,
    `payment` double precision NOT NULL,
    `post_fee` double precision NOT NULL,
    `total_fee` double precision NOT NULL,
    `buyer_message` longtext NOT NULL,
    `seller_memo` longtext NOT NULL,
    `created` datetime,
    `pay_time` datetime,
    `modified` datetime,
    `consign_time` datetime,
    `trade_type` integer NOT NULL,
    `out_sid` varchar(64) NOT NULL,
    `logistics_company_id` bigint,
    `receiver_name` varchar(25) NOT NULL,
    `receiver_state` varchar(16) NOT NULL,
    `receiver_city` varchar(16) NOT NULL,
    `receiver_district` varchar(16) NOT NULL,
    `receiver_address` varchar(128) NOT NULL,
    `receiver_zip` varchar(10) NOT NULL,
    `receiver_mobile` varchar(11) NOT NULL,
    `receiver_phone` varchar(20) NOT NULL,
    `openid` varchar(40) NOT NULL,
    `status` integer NOT NULL
)ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
ALTER TABLE `flashsale_trade` ADD CONSTRAINT `logistics_company_id_refs_id_96c2b48e` FOREIGN KEY (`logistics_company_id`) REFERENCES `shop_logistics_company` (`id`);

DROP OR CREATE TABLE `flashsale_order` (
    `id` bigint(20) auto_increment NOT NULL PRIMARY KEY,
    `oid` varchar(40) NOT NULL UNIQUE,
    `sale_trade_id` bigint NOT NULL,
    `item_id` varchar(64) NOT NULL,
    `title` varchar(128) NOT NULL,
    `price` double precision NOT NULL,
    `sku_id` varchar(20) NOT NULL,
    `num` integer,
    `outer_id` varchar(64) NOT NULL,
    `outer_sku_id` varchar(20) NOT NULL,
    `total_fee` double precision NOT NULL,
    `payment` double precision NOT NULL,
    `sku_name` varchar(256) NOT NULL,
    `pic_path` varchar(512) NOT NULL,
    `created` datetime,
    `modified` datetime,
    `pay_time` datetime,
    `consign_time` datetime,
    `status` integer NOT NULL
)ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
ALTER TABLE `flashsale_order` ADD CONSTRAINT `sale_trade_id_refs_id_c02a6ed1` FOREIGN KEY (`sale_trade_id`) REFERENCES `flashsale_trade` (`id`);

CREATE INDEX `flashsale_register_ac05f004` ON `flashsale_register` (`cus_uid`);
CREATE INDEX `flashsale_customer_fbfc09f1` ON `flashsale_customer` (`user_id`);
CREATE INDEX `flashsale_customer_7b0b2696` ON `flashsale_customer` (`nick`);
CREATE INDEX `flashsale_customer_e7ae4e55` ON `flashsale_customer` (`mobile`);
CREATE INDEX `flashsale_customer_3904588a` ON `flashsale_customer` (`email`);
CREATE INDEX `flashsale_customer_3d05d59a` ON `flashsale_customer` (`openid`);
CREATE INDEX `flashsale_customer_9ac2212` ON `flashsale_customer` (`unionid`);
CREATE INDEX `flashsale_trade_e99ab0` ON `flashsale_trade` (`buyer_id`);
CREATE INDEX `flashsale_trade_9def0345` ON `flashsale_trade` (`pay_time`);
CREATE INDEX `flashsale_trade_96e3648` ON `flashsale_trade` (`logistics_company_id`);
CREATE INDEX `flashsale_trade_5e00a4b8` ON `flashsale_trade` (`receiver_mobile`);
CREATE INDEX `flashsale_trade_c9ad71dd` ON `flashsale_trade` (`status`);
CREATE INDEX `flashsale_order_5a4b9a84` ON `flashsale_order` (`sale_trade_id`);
CREATE INDEX `flashsale_order_9def0345` ON `flashsale_order` (`pay_time`);
CREATE INDEX `flashsale_order_c9ad71dd` ON `flashsale_order` (`status`);
COMMIT;

