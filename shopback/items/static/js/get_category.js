function Category() {
    this.items = items;
    //this.items	= {
    //'0':{1:'亲子装',8:'女装',9:'童装'},
    //'0,1':{1:'上衣',2:'裙裤',3:'套装'},
    //'0,8':{11:'上装',12:'下装',13:'套装',14:'连衣裙',15:'外套',16:'配件'},
    //'0,9':{11:'上装',12:'下装',13:'套装',14:'连衣裙',15:'外套',16:'配件',17:'哈衣',18:'亲子装'},
    //'0,8,11':{1:'上装'},
    //'0,8,12':{1:'下装'},
    //'0,8,13':{1:'套装'},
    //'0,8,14':{1:'连衣裙'},
    //'0,8,15':{1:'外套'},
    //'0,8,16':{1:'配件'},
    //'0,9,11':{1:'上装'},
    //'0,9,12':{1:'下装'},
    //'0,9,13':{1:'套装'},
    //'0,9,14':{1:'连衣裙'},
    //'0,9,15':{1:'外套'},
    //'0,9,16':{1:'配件'},
    //'0,9,17':{1:'哈衣'},
    //'0,9,18':{1:'亲子装'},
    //'0,9,18,1':{1:'亲子装'}
    //};
}

Category.prototype.find	= function(id) {
    if(typeof(this.items[id]) == "undefined")
	return false;
    return this.items[id];
};

Category.prototype.getName = function(loc_id, selected_id){
    var json = this.find(loc_id);
    if(json)
        return json[selected_id] || '';
    return '';
};


Category.prototype.fillOption = function(el_id, loc_id, selected_id) {
    var el = $('#'+el_id);
    var json = this.find(loc_id);
    if (json) {
	var index = 1;
	var selected_index = 0;
	$.each(json , function(k , v) {
            var extra = '';
	    if (k == selected_id) {
                extra = ' selected="selected"';
		selected_index = index;
	    }
            el.append('<option value="'+k+'"'+extra+'>'+v+'</option>');
	    index++;
	});
	el.attr('selectedIndex' , selected_index);
    }
    el.select2('val', selected_id);
};
