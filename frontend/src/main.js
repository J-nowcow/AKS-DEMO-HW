// 프론트엔드 OpenTelemetry는 선택사항 - 백엔드 자동 계측만으로도 충분!

import Vue from 'vue'
import App from './App.vue'

Vue.config.productionTip = false

new Vue({
  render: h => h(App)
}).$mount('#app') 