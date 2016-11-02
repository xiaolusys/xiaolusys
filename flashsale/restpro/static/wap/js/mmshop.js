/**
 * Created on 3/7/16.
 * 代理店铺商品展示
 */

var mm_linkid_for_shop = getUrlParam('mm_linkid');
var link_ufrom = getUrlParam('ufrom');

var mmshopCategory = '';

$(document).ready(function () {
    console.log('link', mm_linkid_for_shop);
    $('.female-zone').click(function () {
        mmshopCategory = 'female';
        // 2016.3.30更换为跳转到商城页面
        location.href = 'http://m.xiaolumeimei.com/nvzhuang.html?mm_linkid=' + mm_linkid_for_shop + '&ufrom=' + link_ufrom;
        //nextShopPage = GLConfig.baseApiUrl + GLConfig.mama_shop;//第一页初始化
        //$(".active-bar").animate({left: '0%'});// 选中条动画
        //
        //$('.products-div').remove();
        //
        //get_mama_shop_info();
        //$(window).scroll(function () {
        //    loadData(get_mama_shop_info);// 更具页面下拉情况来加载数据
        //});
    });

    $('.child-zone').click(function () {
        mmshopCategory = 'child';
        location.href = 'http://m.xiaolumeimei.com/chaotong.html?mm_linkid=' + mm_linkid_for_shop + '&ufrom=' + link_ufrom;
        //nextShopPage = GLConfig.baseApiUrl + GLConfig.mama_shop;//第一页初始化
        //$(".active-bar").animate({left: '196%'});// 选中条动画
        //
        //$('.products-div').remove();
        //
        //get_mama_shop_info();
        //$(window).scroll(function () {
        //    loadData(get_mama_shop_info);// 更具页面下拉情况来加载数据
        //});
    });


});

