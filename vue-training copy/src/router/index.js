import { createRouter, createWebHistory } from 'vue-router';
import { supabase } from '../supabase'; // 引入 supabase 客戶端

// 引入您需要的元件作為路由頁面
import Home from '../views/home.vue'; // 待會會建立
import Login from '../views/login.vue'; // 您現有的 login.vue
import Predict from '../views/predict.vue'; // 預測頁面元件
import History from '../views/history.vue'; // 歷史紀錄頁面元件
import Profile from '../views/profile.vue'; // 使用者個人資料頁面元件
import App from '../App.vue';

const router = createRouter({
  // 使用 HTML5 History 模式
  history: createWebHistory(import.meta.env.BASE_URL), 
  routes:[
    {
      path: '/',
      name: 'Home',
      component: Home // 首頁的元件
    },
    {
      path: '/login',
      name: 'Login',
      component: Login // 登入/註冊頁面
    },
    {
      path: '/predict',
      name: 'Predict',
      component: Predict,
      meta: { requiresAuth: true } // 需要登入才有辦法跳到 predict page
    },
    {
      path: '/history',
      name: 'History',
      component: History,
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'Profile',
      component: Profile,
      meta: { requiresAuth: true }
    }
  ]
})

// 2. 設定導航守衛 (Navigation Guard)
// 用於檢查使用者是否登入，以保護需要驗證的路由
router.beforeEach(async (to, from, next) => {
  // next 執行要去的地方
  // 檢查目標路由是否需要身份驗證
  if (to.meta.requiresAuth){

    // 獲取當前的 Supabase Session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session){
      // 如果有 Session（已登入），則允許前往目標頁面
      next(); 
    } else {
      // 如果沒有 Session（未登入），則強制導向登入頁面
      console.log ('未登入，請先登入');
      next({ name: 'Login' }); 
    }
  }else {
    // 如果目標路由不需要身份驗證（如 /login），則直接放行
    next(); 
  }
})

export default router;

