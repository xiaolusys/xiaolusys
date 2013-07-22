alter table shop_purchases_relationship add index(outer_id,outer_sku_id);

ALTER TABLE shop_purchases_purchase AUTO_INCREMENT=10001;

ALTER TABLE shop_purchases_storage AUTO_INCREMENT=10001;

ALTER TABLE shop_purchases_storage  ENGINE=InnoDB;

ALTER TABLE shop_purchases_relationship ENGINE=InnoDB;

ALTER TABLE shop_purchases_storageitem  ENGINE=InnoDB;

ALTER TABLE shop_purchases_payment_item ENGINE=InnoDB;

ALTER TABLE shop_purchases_item ENGINE=InnoDB;

ALTER TABLE shop_purchases_purchase ENGINE=InnoDB;
