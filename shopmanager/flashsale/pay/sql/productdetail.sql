CREATE TABLE `flashsale_productdetail` (
    `product_id` bigint NOT NULL PRIMARY KEY,
    `head_imgs` longtext NOT NULL,
    `content_imgs` longtext NOT NULL
)ENGINE=MyISAM DEFAULT CHARSET=utf8;

ALTER TABLE `flashsale_productdetail` ADD CONSTRAINT `product_id_refs_id_19ee8fe7` FOREIGN KEY (`product_id`) REFERENCES `shop_items_product` (`id`);

