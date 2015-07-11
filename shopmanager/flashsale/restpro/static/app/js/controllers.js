function PhoneListCtrl($scope, $http) {
	
  $http.jsonp('http://192.168.1.6:8888/static/app/phones/phones.json?callback=JSONP_CALLBACK').success(function(data){
  	console.log('jsonp:',data);
    $scope.phones = data;
  });

  $scope.orderProp = 'age';
}

PhoneListCtrl.$inject = ['$scope', '$http'];

function PhoneDetailCtrl($scope, $routeParams, $http) {
  $http.get('phones/' + $routeParams.phoneId + '.json').success(function(data) {
    $scope.phone = data;
  });
}

PhoneDetailCtrl.$inject = ['$scope', '$routeParams', '$http'];


function RegisterCtrl($scope, $routeParams, Register) {
  
  $scope.phones = Register.query();
}

PhoneDetailCtrl.$inject = ['$scope', '$routeParams'];


