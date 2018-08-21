var app = new Vue({
  el: '#app',
  data: {
    'data': ''
  }
})

Vue.http.get('/sale/daystats/yunying/?json').then((response) => {
    // success callback
    app.data = response.data
    console.log(app.data)
  }, (response) => {
    // error callback
});