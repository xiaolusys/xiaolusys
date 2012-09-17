/**
 * Created by IntelliJ IDEA.
 * User: zfz
 * Date: 2/7/12
 * Time: 4:41 PM
 * To change this template use File | Settings | File Templates.
 */

goog.provide('autolist');


goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.array');
goog.require('goog.style');

goog.require('goog.ui.Dialog');

goog.provide('autolist.Dialog');
/** @constructor */
autolist.Dialog = function (parent) {
    this.parent = parent;
    this.dialog = new goog.ui.Dialog();
    this.init();
}


autolist.Dialog.prototype.init = function () {
	dialog = this;
    var callback = function(data) {
    	var options_str = '' 
    	for(var i=0; i<data.length;i++){ 
    		options_str += '<option value="'+data[i]+'">'+data[i]+'</option>'
    	} 
    	dialog.dialog.setContent(
	        '<div class="control-group">' +
		    '<label class="control-label">选中宝贝：</label>' +
		    '<div class="controls">' +
	            '<img id="id-product-img"/>' +
	            '</div>' +
	            '</div>' +
		    '<div class="control-group">' +
		    '<label class="control-label">上架星期</label>' +
		    '<div class="controls">' +
		    '<select id="id-select-week">' +
	            '<option value="0">请选择</option>' +
	            '<option value="1">周 1</option>' +
	            '<option value="2">周 2</option>' +
	            '<option value="3">周 3</option>' +
	            '<option value="4">周 4</option>' +
	            '<option value="5">周 5</option>' +
	            '<option value="6">周 6</option>' +
	            '<option value="7">周 日</option>' +
	            '</select>' +
	            '</div>' +
		    '</div>' +
	        '<div class="control-group">' +
		    	'<label class="control-label">详细时间：</label>' +
		    	'<div class="controls">' +
	            '<select id="id-list-time">' +
	            	options_str+
	            '</select>' +
	            '</div>' +
	            '</div>');
	    dialog.dialog.setTitle('修改上架时间');
	    dialog.dialog.setButtonSet(new goog.ui.Dialog.ButtonSet()
	            .addButton({key: 'OK', caption: "提交"},true,false));
	
	    goog.events.listen(dialog.dialog, goog.ui.Dialog.EventType.SELECT, dialog);
    };
  
    getJSON('/app/autolist/timeslots/',callback,'GET',{});
}

autolist.Dialog.prototype.show = function(data) {
    this.dialog.setVisible(true);
    var imgDom = goog.dom.getElement("id-product-img");
    imgDom.src = data["img_src"];
}

autolist.Dialog.prototype.handleEvent= function (e) {
    if (e.key == 'OK') {
	var weekDom = goog.dom.getElement("id-select-week");
	var timeDom = goog.dom.getElement("id-list-time");
        var retval = this.parent.changeListTime(weekDom.value, timeDom.value);
        if (retval == false) {
            return false;
        }
	weekDom.value="0";
	timeDom.value="22:00";
    }
    return true;
}

goog.provide('autolist.ClickCell');
/** @constructor */
autolist.ClickCell = function (cellDom, parent) {
    this.parent = parent;
    this.cell = cellDom;
    this.dialogButton = this.cell.children[0];
    
    goog.events.listen(this.cell, goog.events.EventType.MOUSEOVER, this);
    goog.events.listen(this.cell, goog.events.EventType.MOUSEOUT, this);
    goog.events.listen(this.dialogButton, goog.events.EventType.CLICK, this);
}

autolist.ClickCell.prototype.showDialog = function (data) {
    this.parent.showDialog(data);
}
    

autolist.ClickCell.prototype.handleEvent = function (e) {
	
    if (e.type == goog.events.EventType.MOUSEOVER) {
	this.cell.children[0].style.display = "block";
	this.cell.children[1].style.display = "none";
	return;
    }
    if (e.type == goog.events.EventType.MOUSEOUT) {
	this.cell.children[0].style.display = "none";
	this.cell.children[1].style.display = "block";
	return;
    }
    if (e.type == goog.events.EventType.CLICK) {
	var targetDom = e.currentTarget;
	var num_iid = targetDom.getAttribute("num_iid");
	var img_src = targetDom.getAttribute("img_src");
	var data = {"num_iid":num_iid, "img_src":img_src};
	this.showDialog(data);
	return;
    }
}

goog.provide('autolist.ItemList');
/** @constructor */
autolist.ItemList = function () {
    this.recoItems = goog.dom.getElementsByClass('time-select');
    for(var i=0; i<this.recoItems.length; ++i) {
		new autolist.ClickCell(this.recoItems[i], this);
    }
    this.curr_iid = null;

    this.dialog = new autolist.Dialog(this);
}

autolist.ItemList.prototype.changeListTime = function (weekday, time) {
    if (weekday == '0' || time == "") {
	return false;
    }
    
    var url = "/app/autolist/scheduletime/";
    var num_iid = this.curr_iid;
    var callback = function(res) {
	var dom_id = "id-scheduled-"+num_iid;
        var dom = goog.dom.getElement(dom_id);
	if (parseInt(weekday) == 7) {
	    dom.innerHTML = "<p>周 日</p><p>" + res["list_time"] + "</p>";
	} else {
            dom.innerHTML = "<p>周 "+ weekday +"</p><p>" + res["list_time"] + "</p>";
	}
    };
    var method = 'POST';
    var data = {num_iid:num_iid, list_weekday:weekday, list_time:time, task_type:"listing"};
    getJSON(url,callback,method,data);
}

autolist.ItemList.prototype.showDialog = function (data) {
    this.curr_iid = data["num_iid"];
    this.dialog.show(data);
}

goog.provide('autolist.ListModify');
/** @constructor */
autolist.ListModify = function () {
    this.recoItems = goog.dom.getElementsByClass('time-select');
    for(var i=0; i<this.recoItems.length; ++i) {
		if (this.recoItems[i].children.length==2){
			new autolist.ClickCell(this.recoItems[i], this);
		}
    }
    this.curr_iid = null;
    this.dialog = new autolist.Dialog(this);
}


autolist.ListModify.prototype.changeListTime = function (weekday, time) {
    if (weekday == '0' || time == "") {
	return false;
    }
    
    var url = "/app/autolist/scheduletime/";
    var num_iid = this.curr_iid;
    var callback = function(res) {
		if (res["list_time"]!="undefined"){
			document.location.reload();
		}
    };
    var method = 'POST';
    var data = {num_iid:num_iid, list_weekday:weekday, list_time:time, task_type:"listing"};
    getJSON(url,callback,method,data);
}

autolist.ListModify.prototype.showDialog = function (data) {
    this.curr_iid = data["num_iid"];
    this.dialog.show(data);
}

goog.provide('autolist.TimeTable');

/** @constructor */
autolist.TimeTable = function () {
    this.weekdays = goog.dom.getElementsByClass('timetable');
    for(var i=0; i<this.weekdays.length; ++i) {
        goog.events.listen(this.weekdays[i], goog.events.EventType.CLICK, this);
    }
}

autolist.TimeTable.prototype.handleEvent = function (e) {
    if (e.type == goog.events.EventType.CLICK) {
        console.log(e.currentTarget.getAttribute("day"));
    }
}


goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');

function getJSON(url, fun, method, data) {
    method = method || 'GET';
    data = data || {};
    var callback = function(e) {
        var xhr = e.target;
        try {
            var res = xhr.getResponseJson();
            fun(res);
        } catch (err) {
            console.log('Error: (ajax callback) - ', err);
        }
    };
    var content = goog.uri.utils.buildQueryDataFromMap(data);
	
    var csrftokenDiv = goog.dom.getElement("id-csrftoken");
    var csrftoken = goog.dom.getElementsByTagNameAndClass("INPUT", null, csrftokenDiv)[0].value;
    var header = {"X-CSRFToken": csrftoken};
    
    if (method == 'GET') {
        goog.net.XhrIo.send(url + '?' + content, callback, method);
    } else {
        goog.net.XhrIo.send(url, callback, method, content, header);
    }
}

