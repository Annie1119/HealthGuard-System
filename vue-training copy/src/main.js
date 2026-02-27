import './assets/main.css'
import { createApp } from 'vue';
import App from './App.vue';
import router from './router'; // 引入剛剛設定好的路由

const app = createApp(App);

app.use(router); // 將 router 掛載到應用程式

app.mount('#app');

