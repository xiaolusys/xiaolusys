var ItemRank = function ()  {
  this.initialize();
  this.registerEvents();
};

ItemRank.prototype.initialize = function () {
  this.start_dp    = $('#start_dp'); 
  this.end_dp      = $('#end_dp');
  this.selects     = $('.key-words-selects');
  this.nicks       = $('.nicks');
  this.plus_key    = $('.plus-keyword');
  this.plus_nick   = $('.plus-nick');
  this.refresh     = $('.refresh');
  this.charts_area = $('.charts-area'); 
  this.cancel      = $('.cancel');

  this.initDatePickers(this.start_dp);
  this.initDatePickers(this.end_dp);

  this.getCharts();
}

ItemRank.prototype.registerEvents = function () {
  var that = this;

  this.plus_nick.click(function (e) {
    var template = $(that.nicks.find('.nick-control')[0]).clone(true)
    template.find('input').val('');
    template.insertBefore(that.nicks.find('.btn'));
  });

  this.plus_key.click(function (e)  {
    $(that.selects.find('.select-control')[0]).clone(true).insertBefore(that.selects.find('.btn'));
  });

  this.cancel.click(function (e)  {
    if ($(this).parent().siblings().length <= 1)
      alert('At least one keyword');
    else  {
      $(this).parent().remove();
    }
  });

  this.refresh.click(function (e) {
    that.getCharts(); 
  }); 
}

ItemRank.prototype.initDatePickers = function (dp)  {
  dp.datepicker({
    format: 'yyyy-mm-dd', 
  }); 
}

ItemRank.prototype.getCharts = function ()  {
  var that = this;
  var URL  = '/search/rank/chart';
  var date = this.createDate();
  //URL = URL+'/'+date.today+'/'+date.yesterday;
  URL = URL+'/2012-03-17/2012-03-18/'
  var params = {
    nicks    : this.getNicks(),
    keywords : this.getKeyWords(),
    format   : 'json'
  };
  $.getJSON(URL, params, function (res) {
    that.refreshCharts(res);
  });
}

ItemRank.prototype.refreshCharts = function (res) {
  if (res.code == 0)  {
    this.charts_area.empty();

    var that     = this;
    var response = res.response_content;
    var items    = res.items;
    var i        = 0;
    var length   = response.length;
    var charts   = [];


    for (; i<length; i++) {
      var temp_res = response[i];
      temp_res['tooltip'] = {
        useHTML: true,
        formatter: function ()  {
          var pic_url = that.getPicUrl(items, this.series.name) || '';
          var template = [
            '<div class="tooltip-img">',
              '<img src="'+ pic_url+ '"/>',
            '</div>',
          ].join('');
          return template;
        },
        borderColor: 'rgba(0,0,0,0)',
        backgroundColor: 'rgba(0,0,0,0)',
        shadow: false,
      }
      var template = $('<div id="chart_'+(i+1)+'"></div>') 
      this.charts_area.append(template);
      charts.push(new Highcharts.Chart(temp_res));
    }
  } else  {
    alert('Failed'); 
  }
}

ItemRank.prototype.getPicUrl = function (items, item_id)  {
  var i = 0;
  var length = items.length;
  for(; i<length; i++)  {
    var item = items[i];
    if (item.item_id == item_id)  {
      return item.pic_url;
    }
  }
}

ItemRank.prototype.createDate = function () {
  var today = new Date();
  var yesterday = new Date();
  yesterday.setTime(today - 86400000);
  return {
    today: today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate(),
    yesterday: yesterday.getFullYear()+'-'+(yesterday.getMonth()+1)+'-'+yesterday.getDate(),
  }
}

ItemRank.prototype.getNicks = function () {
  inputs = this.nicks.find('input');
  var nicks = [];
  var i = 0;
  var length = inputs.length;
  for (; i<length; i++) {
    nicks.push(inputs[i].value); 
  }
  nicks = nicks.join(',');
  return nicks;
}

ItemRank.prototype.getKeyWords = function ()  {
  selects = this.selects.find('select');
  var keywords = [];
  var i = 0;
  var length = selects.length;
  for (; i< length; i++)  {
    var select = selects[i];
    keywords.push(select.options[select.selectedIndex].text);
  }
  keywords = keywords.join(',');
  return keywords;
}

$(function () {
  var itemrank = new ItemRank();
});
