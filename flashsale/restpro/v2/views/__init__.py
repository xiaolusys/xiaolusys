from .category import SaleCategoryViewSet
from .lesson import LessonTopicViewSet, LessonViewSet, InstructorViewSet, \
    LessonAttendRecordViewSet, WeixinSNSAuthJoinView
from .product import ProductViewSet
from .modelproduct import ModelProductV2ViewSet
from .packageskuitem import PackageSkuItemView
from .shoppingcart import ShoppingCartViewSet
from .trade import SaleTradeViewSet, SaleOrderViewSet
from .xiaolumm import MamaFortuneViewSet, CarryRecordViewSet, OrderCarryViewSet, \
    ClickCarryViewSet, AwardCarryViewSet, ActiveValueViewSet, ReferalRelationshipViewSet, \
    GroupRelationshipViewSet, UniqueVisitorViewSet, XlmmFansViewSet, OrderCarryVisitorView, \
    DailyStatsViewSet, PotentialFansView, ModelProductViewSet
from .verifycode_login import *
from .misssion import MamaMissionRecordViewset
from .kdn_wuliu import *
from .checkin import CheckinViewSet
from .qrcode import QRcodeViewSet
from .views_coupon import CouponTransferRecordViewSet
from .urlredirect import URLRedirectViewSet
from .wdt import WangDianTongViewSet
