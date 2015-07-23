BEGIN;
CREATE TABLE `suplychain_flashsale_mygroup` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(80) NOT NULL UNIQUE
)ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8
;
CREATE TABLE `suplychain_flashsale_myuser` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` bigint NOT NULL UNIQUE,
    `group_id` bigint NOT NULL
)ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8
;
ALTER TABLE `suplychain_flashsale_myuser` ADD CONSTRAINT `group_id_refs_id_36d7bd0a` FOREIGN KEY (`group_id`) REFERENCES `suplychain_flashsale_mygroup` (`id`);
ALTER TABLE `suplychain_flashsale_myuser` ADD CONSTRAINT `user_id_refs_id_99e920ef` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
COMMIT;
