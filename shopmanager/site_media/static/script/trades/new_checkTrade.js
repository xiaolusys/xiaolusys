function openwin33(){

  //alert("333");
window.open ("/trades/check_order/", "newwindow", "height=800, width=800, top=300,left=400,toolbar =no, menubar=no, scrollbars=no, resizable=no, location=no, status=no") //写成一行


}
function openwin(symbol_link){

    //alert(symbol_link);
   //window.showModalDialog('http://www.jb51.net,'脚本之//家','dialogWidth:400px;dialogHeight:300px;dialogLeft:200px;dialogTop:150px;center:yes;help:yes;resizable:yes;status:yes') ;

var obj = new Object();
          obj.name="51js";
 //window.showModalDialog("/trades/check_order/"+symbol_link,obj,"dialogWidth=800px;dialogHeight=700px;dialogLeft:450px;status=no; center:yes ;location:no ");
window.open("/trades/check_order/"+symbol_link,obj,"width=800px,height=700px,left:450px,status=no, center:yes ,location:no ");
}


function showlayer(symbol_link) {
    url = '/trades/check_order/' +symbol_link;
    layer.open({
        type: 2,
        title: "订单审核页面",
        shadeClose: true,
        shade: 0.8,
        
        area: ['1000px', '600px'],
        content: url
    });
}



