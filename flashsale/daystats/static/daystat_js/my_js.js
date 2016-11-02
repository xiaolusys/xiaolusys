/**
 * Created by yann on 15-8-3.
 */

$(function () {

    setTimeout(get_data, 4000);
    setTimeout(get_data2, 2000);
    setTimeout(get_data3, 2000);
});
function get_data() {
    var task_id = $("#task_id_repeat").val();
    $.ajax({
        url: "/djcelery/" + task_id + "/status/", //这里是静态页的地址
        method: "GET", //静态页用get方法，否则服务器会抛出405错误
        success: function (res) {
            console.log("1", res.task.status);
            if (res.task.status == "SUCCESS") {
                var tb = $('#repeat_table');
                var result_data = eval(res.task.result);
                $("#repeat_table thead").eq(0).nextAll().remove();
                $.each(result_data, function (index, dd) {
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

function get_data2() {
    var task_id = $("#task_id_2").val();
    $.ajax({
        url: "/djcelery/" + task_id + "/status/", //这里是静态页的地址
        method: "GET", //静态页用get方法，否则服务器会抛出405错误
        success: function (res) {
            console.log("2", res.task.status);
            if (res.task.status == "SUCCESS") {
                var tb = $('#data-table-people');
                var result_data_people = eval(res.task.result);
                console.log(result_data_people);
                $("#data-table-people thead").eq(0).nextAll().remove();
                $.each(result_data_people, function (index, dd) {
                    tb.append("<tr><td>" + dd[0] + "月份</td><td>" + dd[1] + "</td><td>" + dd[4] + "</td><td>" + dd[2] + "</td><td>" + dd[3] + "</td></tr>");
                });
            } else {
                setTimeout(get_data2, 2000);
            }
        }
    });
}


function get_data3() {
    var task_id = $("#task_id_sale").val();
    $.ajax({
        url: "/djcelery/" + task_id + "/status/", //这里是静态页的地址
        method: "GET", //静态页用get方法，否则服务器会抛出405错误
        success: function (res) {
            console.log("3",res.task.status);
            if (res.task.status == "SUCCESS") {

                var tb = $('#data-table-sale');
                var result_data = eval(res.task.result);

                $("#data-table-sale thead").eq(0).nextAll().remove();
                $.each(result_data, function (index, dd) {
                    tb.append("<tr><td>" + dd[0] + "月份</td><td>" + dd[1] + "</td><td>" + dd[2] + "</td><td>" + dd[4] + "</td><td>" + dd[3] + "</td></tr>");
                });

            } else {
                setTimeout(get_data3, 2000);
            }
        }
    });
}
