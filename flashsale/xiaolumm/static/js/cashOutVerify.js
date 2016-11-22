var approveCashOut = function (id) {
    layer.confirm('确定' + id + '提现么？', {
        btn: ['确定', '取消'] //按钮
    }, function () {
        var btn = $(".cashOut" + id);
        if (btn.hasClass('loading')) {
            return
        }
        btn.addClass('loading');
        var coupon_url = "/m/cash_out_verify";
        $.ajax({
            url: coupon_url,
            success: couponCallBack,
            data: {'cash_out_id': id, 'action': 'approved'},
            type: 'post',
            error: function (err) {
                var resp = JSON.parse(err.responseText);
                if (resp.detail) {
                    layer.msg(resp.detail);
                }
            }
        });
        function couponCallBack(res) {
            btn.removeClass('loading');
            layer.msg(res.info);
            btn.parent().parent().remove()
        }
    }, function () {
    });
};

var rejectCashOut = function (id) {
    layer.confirm('拒绝' + id + '提现么？', {
        btn: ['确定', '取消'] //按钮
    }, function () {
        var btn = $(".cashOut" + id);
        if (btn.hasClass('loading')) {
            return
        }
        btn.addClass('loading');
        var coupon_url = "/m/cash_out_verify";
        $.ajax({
            url: coupon_url,
            data: {'cash_out_id': id, 'action': 'rejected'},
            type: 'post',
            success: couponCallBack,
            error: function (err) {
                var resp = JSON.parse(err.responseText);
                if (resp.detail) {
                    layer.msg(resp.detail);
                }
            }
        });
        function couponCallBack(res) {
            console.log(res);
            btn.removeClass('loading');
            layer.msg(res.info);
            btn.parent().parent().remove()
        }
    }, function () {
    });
};
