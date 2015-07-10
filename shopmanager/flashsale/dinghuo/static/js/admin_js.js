/**
 * Created by yann on 15-7-10.
 */
function show_pic(id) {
    var gallery = $('.popup-gallery');
    var gallery_img = $('.popup-gallery a');
    gallery_img.remove()
    $.get('/sale/dinghuo/show_pic/' + id, function (result_data) {
        var obj = result_data.split(",");
        $.each(obj, function (index, value) {
            gallery.append('<a class="example-image-link" style="display:None" href="'+ value +'" data-lightbox="example-1">ttt</a>');
        });
        var example = $(".example-image-link");
        if(example.length >0){
            example.trigger("click");
        }

    });


}