
var mainServ = angular.module("MainService",['XLProductService']);

mainServ.controller("PosterCtrl",[ '$scope', 'Product',function($scope,Product){
	
	$scope.posters = Product.getList();
	console.log('debug poster end',$scope.posters);
}]);

