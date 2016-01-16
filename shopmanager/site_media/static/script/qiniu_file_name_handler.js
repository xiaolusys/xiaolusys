/**
 * Created by jishu_linjie on 1/16/16.
 */
function FileNameHandler(file_name, suffix) {
    // 处理上传字符串将字符串中的非正常字符删除
    console.log('file_name:',file_name);
    var name = file_name.replace(/[^\u4E00-\u9FA5\w\.]/g, '');
    var timestamp = new Date().getTime();// 添加上传时间戳
    var key = timestamp + name;
    return suffix + key
}
