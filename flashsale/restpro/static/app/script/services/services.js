angular.module('XLMMServices', ['ngResource'])
	.factory('Register', function($resource){
	  return $resource('register/:registerId.json', {}, {
	    query: {method:'GET', params:{registerId:'register'}, isArray:true}
	  });
	})
	//.factory('User', function($resource){
//	  return $resource('users/:userId.json', {}, {
//	    query: {method:'GET', params:{userId:'users'}, isArray:true}
//	  });
//	})
	;