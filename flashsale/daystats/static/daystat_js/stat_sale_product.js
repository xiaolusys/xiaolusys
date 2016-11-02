String.format = function () {
    if (arguments.length == 0)
        return null;
    var str = arguments[0];
    for (var i = 1; i < arguments.length; i++) {
        var re = new RegExp('\\{' + (i - 1) + '\\}', 'gm');
        str = str.replace(re, arguments[i]);
    }
    return str;
};
function Calc_stats_data() {


    var nv_rows = $("#data-table-result > tbody > tr");
    var child_rows = $("#data-table-child-result > tbody > tr");
    var num1 = 0, num2 = 0, num3 = 0, num4 = 0, num5 = 0, num6 = 0, num7 = 0, num8= 0, num9= 0;
    for (var i = 0; i < nv_rows.length; i++) {
        row = nv_rows[i];
        num1 += parseInt(row.cells[1].innerText);
        num2 += parseInt(row.cells[2].innerText);
        num3 += parseInt(row.cells[3].innerText);
        num4 += parseInt(row.cells[4].innerText);
        num5 += parseInt(row.cells[5].innerText);
        num6 += parseInt(row.cells[6].innerText);
        num7 += parseInt(row.cells[7].innerText);
        num8 += parseInt(row.cells[8].innerText);
        num9 += parseInt(row.cells[9].innerText);
    }
    var html = "<tr><td>汇总</td><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td><td>{7}</td><td>{8}</td></tr>";
    var format_html = String.format(html, num1, num2, num3, num4, num5, num6, num7, num8, num9);
    $("#data-table-result").append(format_html);

    var child_num1 = 0, child_num2 = 0, child_num3 = 0, child_num4 = 0, child_num5 = 0,
        child_num6 = 0, child_num7 = 0, child_num8 = 0, child_num9 = 0, child_num10 = 0, child_num11 = 0;
    for (var i = 0; i < child_rows.length; i++) {
        row = child_rows[i];
        child_num1 += parseInt(row.cells[1].innerText);
        child_num2 += parseInt(row.cells[2].innerText);
        child_num3 += parseInt(row.cells[3].innerText);
        child_num4 += parseInt(row.cells[4].innerText);
        child_num5 += parseInt(row.cells[5].innerText);
        child_num6 += parseInt(row.cells[6].innerText);
        child_num7 += parseInt(row.cells[7].innerText);
        child_num8 += parseInt(row.cells[8].innerText);
        child_num9 += parseInt(row.cells[9].innerText);
        child_num10 += parseInt(row.cells[10].innerText);
        child_num11 += parseInt(row.cells[11].innerText);
    }
    var child_html = "<tr><td>汇总</td><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td><td>{7}</td><td>{8}</td><td>{9}</td><td>{10}</td></tr>";
    var child_format_html = String.format(child_html, child_num1, child_num2, child_num3, child_num4, child_num5, child_num6, child_num7, child_num8, child_num9, child_num10, child_num11);
    $("#data-table-child-result").append(child_format_html);

}

Calc_stats_data();


