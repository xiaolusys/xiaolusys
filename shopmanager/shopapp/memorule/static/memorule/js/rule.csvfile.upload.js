$(document).ready(function(){
       $(document.body).append('<div id="upload_csvfile" style="display:none;margin:auto;"></div>');
       $('#upload_csvfile').append('<div class="upload_submit" ></div>');
       $('.upload_submit').append('<div style="height:150px;width:600px;"><img src="/static/img/splitrule.png" width="580" height="150px;"></div>')
       $('.upload_submit').append('<button id="attach_files" style="background:#999;color:white;width:200px;'+
               'height:40px;display:inline;">导入拆分规则CSV文件</button>')
       $('.upload_submit').append('<span class="import_status" style="display:none;color:red;">文件导入失败，请检查文件格式！</span>')

       $('.upload-csvfile').click(function(e){
           e.preventDefault();
           
           $("#attach_files").upload({
               name: 'attach_files',
               action: '/app/memorule/composerule/import/',
               enctype: 'multipart/form-data',
               //params: {},
               autoSubmit: true,
               //onSubmit: function() {},
               onComplete: function(e) {
                       var res = $.parseJSON(e);
                       if ( res.code == 0 && res.response_content.success){
                           window.location = res.response_content.redirect_url;
                       }else{
                           $('.import_status').css('display','inline');
                       }
               },
               onSelect: function() {
                       $('.import_status').css('display','none');                      
               }
           });
           $('#upload_csvfile').dialog({title: "CSV文件导入商品拆分规则",width:'700',height:'300'});
       });
});
