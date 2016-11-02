function Supplier() {
    this.items = suppliers;
	//this.items	= {
	//'0':{1:'supplier1',8:'supplier1',9:'supplier1'}
	//};
}

Supplier.prototype.find	= function(id) {
	if(typeof(this.items[id]) == "undefined")
		return false;
	return this.items[id];
}

Supplier.prototype.fillOption	= function(el_id , loc_id , selected_id) {
	var el	= $('#'+el_id);
	var json	= this.find(loc_id);
	if (json) {
		var index	= 1;
		var selected_index	= 0;
		$.each(json , function(k , v) {
			var option	= '<option value="'+k+'">'+v+'</option>';
			el.append(option);

			if (k == selected_id) {
				selected_index	= index;
			}

			index++;
		})
		//el.attr('selectedIndex' , selected_index);
	}
	el.select2("val", "");
}

