from .base import update_weixin_productstock, task_Update_Weixin_Userinfo,\
    task_Mod_Merchant_Product_Status, pullWXProductTask, \
    pullWaitPostWXOrderTask, pullFeedBackWXOrderTask, \
    syncStockByWxShopTask, syncWXProductNumTask, \
    task_snsauth_update_weixin_userinfo, task_refresh_weixin_access_token
from .subscribe import task_subscribe_or_unsubscribe_update_userinfo
from .xiaolumama import task_create_mama_referal_qrcode_and_response_weixin, \
    task_create_mama_and_response_manager_qrcode,\
    task_weixinfans_update_xlmmfans,\
    task_weixinfans_create_budgetlog,\
    task_get_unserinfo_and_create_accounts, \
    task_activate_xiaolumama, \
    task_create_scan_potential_mama, \
    task_create_or_update_weixinfans_upon_subscribe_or_scan, \
    task_update_weixinfans_upon_unsubscribe
