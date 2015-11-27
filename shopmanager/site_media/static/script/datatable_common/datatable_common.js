/**
 * Created by jishu_linjie on 11/26/15.
 */


function addItem(dom, arr) {
    // 给指定dom<table>标签　添加行数据　arr
    $(dom).dataTable().fnAddData(
        arr
    );
}

function usedataTable(dom, sort_row, asc) {
    // sort_row 表示哪一列初始排序
    // var asc = "asc"
    $(dom).dataTable({
        //"bJQueryUI": true,
        "bRetrieve": true,
        "bAutoWidth": true,//false, //自适应宽度
        "aaSorting": [[sort_row, asc]],
        "iDisplayLength": 50,
        "aLengthMenu": [[20, 50, 100, -1], [20, 50, 100, "All"]],
        //"bInfo":true,
        //"sPaginationType": "full_numbers",
        //"sDom": '<"H"Tfr>t<"F"ip>',
        "oLanguage": {
            "sLengthMenu": "每页 _MENU_ 条",
            "sZeroRecords": "抱歉， 没有找到",
            "sInfo": "从 _START_ 到 _END_ /共 _TOTAL_ 条",
            "sInfoEmpty": "没有数据",
            "sSearch": "搜索",
            "sInfoFiltered": "(从 _MAX_ 条数据中检索)",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "前一页",
                "sNext": "后一页",
                "sLast": "尾页"
            },
            "sZeroRecords": "没有检索到数据",
            "sProcessing": "<img src='/static/img/loading.gif' />"
        }
    });
}