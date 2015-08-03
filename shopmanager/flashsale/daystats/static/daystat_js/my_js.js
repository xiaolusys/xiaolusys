/**
 * Created by yann on 15-8-3.
 */

$(function () {
    var my_data = {"df": $("#f_datepicker").val(), "dt": $("#t_datepicker").val()}
    $.ajax({
        url: "/sale/daystats/stats_sale/", //这里是静态页的地址
        method: "GET", //静态页用get方法，否则服务器会抛出405错误
        data: my_data,
        success: function (res) {
            $("#all_data").html(res);
        }
    });
    $.ajax({
        url: "/sale/daystats/stats_people/", //这里是静态页的地址
        method: "GET", //静态页用get方法，否则服务器会抛出405错误
        data: my_data,
        success: function (res) {
            $("#all_data2").html(res);
        }
    });
    setTimeout(get_data, 4000);
});
function get_data() {
    console.log("get_data");
    var task_id = $("#task_id").val();
    $.ajax({
        url: "/djcelery/" + task_id + "/status/", //这里是静态页的地址
        method: "GET", //静态页用get方法，否则服务器会抛出405错误
        success: function (res) {
            console.log(res.task.status);
            if (res.task.status == "SUCCESS") {
                var tb = $('#repeat_table');
                var result_data = eval(res.task.result);
                $("#repeat_table thead").eq(0).nextAll().remove();
                $.each(result_data, function (index, dd) {
                    console.log(dd);
                    var result_str = "<tr><td>" + dd.month + "月(" + dd.new_user + ")</td>";


                    $.each(dd.user_data, function (index1, dd1) {
                        if (dd1 == "None") {
                            result_str += "<td>-</td>"
                        } else {
                            result_str += "<td>(" + dd1.num + ")" + dd1.rec_num + "</td>";
                        }
                    });
                    result_str += "</tr>";
                    tb.append(result_str);
                });
            } else {
                setTimeout(get_data, 4000);
            }
        }
    });
}
