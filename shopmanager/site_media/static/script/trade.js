var show_hide = function(ev){
	ev  =  ev  ||  window.event;
	var  target    =  ev.target || ev.srcElement;
	var  e_id  = target.getAttribute('e_id');
	var  elt   = $('#'+e_id);
	if (elt.css('display') == 'none'){
		elt.css('display','block');
		$(target).text("折叠");
	}else{
		elt.css('display','none');
		$(target).text("展开");
	}
}