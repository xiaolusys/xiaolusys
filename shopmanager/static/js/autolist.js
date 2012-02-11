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


goog.provide('autolist.Selector');


/** @constructor */
autolist.Selector = function (selector_id, parent) {
    this.selector = goog.dom.getElement(selector_id);
    this.selector.onchange = function () {
        parent.updateSelection();
    };
}

autolist.Selector.prototype.getValue = function () {
    return this.selector.value;
}

autolist.Selector.prototype.clear = function () {
    return this.selector.value = 0;
}


goog.provide('autolist.ItemList');
/** @constructor */
autolist.ItemList = function () {
    this.timeselection = goog.dom.getElement('id-timeslots');
    this.recoItems = goog.dom.getElementsByClass('time-select');
    for(var i=0; i<this.recoItems.length; ++i) {
        goog.events.listen(this.recoItems[i], goog.events.EventType.DBLCLICK, this);
    }
    this.currRow = null;

    this.weekdaySelector = new autolist.Selector('id-select-weekday', this);
    this.timeslotSelector = new autolist.Selector('id-select-timeslot', this);
}

autolist.ItemList.prototype.updateSelection = function () {
    var weekday = this.weekdaySelector.getValue();
    var timeslot = this.timeslotSelector.getValue();

    if (weekday != 0 && timeslot != 0) {
        var url = "/task/"
        var row = this.currRow;
        var callback = function(res) {
            var cell = row.getElementsByClassName('time-select')[0];
            if (cell.tagName == 'TD') {
                cell.innerHTML = "<p>周 "+ res.list_weekday +"</p><p>" + res.list_time + "</p>";
            }
        };
        var method = 'POST';
        console.log(row);
        var data = {num_iid:row.id, title:row.title, num:row.getAttribute('num'),
            list_weekday:weekday, list_time:timeslot, task_type:"listing"};
        console.log(data);
        getJSON(url,callback,method,data);

        this.timeselection.style.display = "none";
        if (this.currRow.tagName == 'TR') {
            goog.dom.classes.addRemove(this.currRow, 'row-highlight', 'row-mark');
        }
    }
}

autolist.ItemList.prototype.handleEvent = function (e) {
    if (e.type == goog.events.EventType.DBLCLICK) {
        console.log(e.currentTarget);
        if (this.currRow != null) {
            goog.dom.classes.remove(this.currRow, "row-highlight");
        }
        this.currRow = e.currentTarget.parentNode;
        console.log('parentNode', this.currRow);

        if (this.currRow.tagName == 'TR') {
            goog.dom.classes.add(this.currRow, "row-highlight");
        }

        this.weekdaySelector.clear();
        this.timeslotSelector.clear();
        this.timeselection.style.display = "block";
        //this.timeselection.style.position = "absolute";

        goog.dom.append(e.currentTarget, this.timeselection);
    }
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

    if (method == 'GET') {
        goog.net.XhrIo.send(url + '?' + content, callback, method);
    } else {
        goog.net.XhrIo.send(url, callback, method, content);
    }
}

