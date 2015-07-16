
var productServ = angular.module('XLProductService',['restangular']); //'XLConfig'

//productServ.config(function(RestangularProvider,XLConfig) {
//	RestangularProvider.setBaseUrl(XLConfig.baseapiurl);
//});

productServ.config(function(RestangularProvider) {
	RestangularProvider.setResponseInterceptor(function(data, operation, what) {
		console.log('debug',data,operation,what);
		if (operation == 'getList') {
			return data;
		}
		return data;
	});
});

productServ.factory('Product',['Restangular',function(Restangular){
	var restAngular = 
      Restangular.withConfig(function(Configurer) {
        Configurer.setBaseUrl('/rest/v1/');
    });
    var _messageService = restAngular.all('products');
    return {
      getList: function() {
      	var resp = _messageService.getList();
      	console.log('debug:',resp);
        return resp;
      }
    }
}]);