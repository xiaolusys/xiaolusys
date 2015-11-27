/**
 * Created by jishu_linjie on 11/21/15.
 * Use this js file must import this src js in the html file
 * <script type="text/javascript" src="http://cdn.hcharts.cn/highcharts/highcharts.js"></script>
 * <script type="text/javascript" src="//cdn.bootcss.com/highcharts/4.1.9/modules/exporting.js"></script>
 */


function highChar(dom, X_axis, Title, Subtitle, Yaxis, series) {
    //　柱状图
    console.log(dom, X_axis, Title, series);
    // http://www.hcharts.cn/test/index.php?from=demo&p=10
    $(dom).highcharts({
        chart: {
            type: 'column'
        },
        title: {
            text: Title
        },
        subtitle: {
            text: Subtitle
        },
        xAxis: {
            categories: X_axis
        },
        yAxis: {
            min: 0,
            title: {
                text: Yaxis
            }
        },
        tooltip: {
            headerFormat: '<span style="font-size:10px">{point.key}</span><table>',
            pointFormat: '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
            '<td style="padding:0"><b>{point.y:.1f} </b></td></tr>',
            footerFormat: '</table>',
            shared: true,
            useHTML: true
        },
        plotOptions: {
            column: {
                pointPadding: 0.2,
                borderWidth: 0
            }
        },
        series: series
    });
}

function pieChart(dom, title, series_name, data) {
    // 饼状图
    $(dom).highcharts({
        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false
        },
        title: {
            text: title
        },
        tooltip: {
            pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    color: '#000000',
                    connectorColor: '#000000',
                    format: '<b>{point.name}</b>: {point.percentage:.1f} %'
                }
            }
        },
        series: [{
            type: 'pie',
            name: series_name,
            data: data
        }]
    });
}

function linechart(dom, X_axis, Title, Subtitle, Yaxis, series) {
    $(dom).highcharts({
        title: {
            text: Title,
            x: -20 //center
        },
        subtitle: {
            text: Subtitle,
            x: -20
        },
        xAxis: {
            categories: X_axis
        },
        yAxis: {
            title: {
                text: Yaxis
            },
            plotLines: [{
                value: 0,
                width: 1,
                color: '#808080'
            }]
        },
        tooltip: {
            valueSuffix: ''
        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle',
            borderWidth: 0
        },
        series: series
    });
}


function timpic_left_right() {
    $(function () {
        $("#left_date_pic").datepicker({
            dateFormat: "yy-mm-dd"
        });
        $("#right_date_pic").datepicker({
            dateFormat: "yy-mm-dd"
        });
    });
}

<!--字符串format函数-->
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

<!-- 获取url 参数　-->
function getUrlParam(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)"); //构造一个含有目标参数的正则表达式对象
    var r = window.location.search.substr(1).match(reg);  //匹配目标参数
    if (r != null) return unescape(r[2]);
    return null; //返回参数值
}