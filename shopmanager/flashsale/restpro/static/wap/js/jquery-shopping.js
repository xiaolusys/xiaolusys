/**
 * Created by yann on 15-7-29.
 */


(function ($) {
    $.extend($.fn, {
        shoping: function (options) {
            var self = this,
                $shop = $('.cart'),
                $body = $('.J-shoping-body')
            var S = {
                init: function () {
                    $(self).data('click', true).live('click', this.addShoping);
                },
                addShoping: function (e) {
                    console.log(e);
                    e.stopPropagation();
                    var $target = $(e.target),
                        id = $target.attr('id'),
                        dis = $target.data('click'),
                        x = $target.offset().left + 30,
                        y = $target.offset().top + 10,
                        X = $shop.offset().left + $shop.width() / 2 - $target.width() / 2 + 10,
                        Y = $shop.offset().top;
                    console.log(dis);
                    if (dis) {
                        if ($('#floatOrder').length <= 0) {
                            $('body').append('<div id="floatOrder"><img src="../images/pro1.jpg" width="25" height="25" /></div>');
                        }

                        var $obj = $('#floatOrder');
                        if (!$obj.is(':animated')) {
                            $obj.css({'left': x, 'top': y}).animate({'left': X, 'top': Y - 80}, 500, function () {
                                $obj.stop(false, false).animate({'top': Y - 20, 'opacity': 0}, 500, function () {
                                    $obj.fadeOut(300, function () {
                                        $obj.remove();
                                        //$target.data('click', false).addClass('dis-click');
                                    });
                                });
                            });
                        }

                    }

                }
            };
            S.init();
        }
    });
})(jQuery);