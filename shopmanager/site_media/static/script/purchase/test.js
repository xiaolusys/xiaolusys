goog.provide('test');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.ui.Zippy');
goog.require('goog.style');
goog.require('goog.ui.Component.EventType');

goog.require('goog.net.XhrIo');
goog.require('goog.uri.utils');

//主控制对象
goog.provide('test.Manager');
/** @constructor */
test.Manager = function () {
	$('#id-purchaseitem-table').dataTable( );
}