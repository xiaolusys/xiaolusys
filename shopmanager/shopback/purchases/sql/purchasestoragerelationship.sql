alter table shop_purchases_relationship add index(outer_id,outer_sku_id);

alter table shop_purchases_paymentitem add index(purchase_id,purchase_item_id);

alter table shop_purchases_paymentitem add index(storage_id,storage_item_id);


ALTER TABLE shop_purchases_purchase AUTO_INCREMENT=10001;

ALTER TABLE shop_purchases_storage AUTO_INCREMENT=10001;


