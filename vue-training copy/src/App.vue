<template>
  <div id="app-container">
    <!-- 只在 /predict 或 /history 且登入後顯示 header -->
    <header v-if="isLoginedIn && (route.path === '/predict' || route.path === '/history')" class="site-header">
      <!-- 左邊 Logo -->
      <router-link to="/" class="logo">HealthGuard🫀</router-link>

      <!-- 右邊按鈕 + 頭貼 -->
      <div class="header-right">
        <nav class="nav-links">
          <RouterLink to="/predict" class="nav-btn">Predict</RouterLink>
          <RouterLink to="/history" class="nav-btn">History</RouterLink>
        </nav>

        <Profile v-if="isLoginedIn && (route.path === '/predict' || route.path === '/history')" />
      </div>
    </header>

    <main class="page-content">
      <RouterView />
    </main>

    <footer
      v-if="route.path === '/' || route.path === '/history'"
      class="site-footer"
    >
      <div class="footer-content">
        <p>© 2025 HealthGuard. All rights reserved.</p>
        <div class="footer-links">
          <a href="#">Privacy Policy</a>
          <a href="#">Terms of Service</a>
          <a href="mailto:foreverannie.1119@gmail.com">Contact</a>
        </div>
      </div>
    </footer>
  </div>
</template>
<!-- <RouterLink>:
  這是 Vue Router 提供的組件，用來替代傳統的 <a> 標籤。
  優點：點擊時不會重新整理整個網頁，只會切換組件，速度非常快（SPA 核心）。 -->
<!-- <RouterView />:
位於 <main> 標籤內。
這是動態內容的出口。當你點擊上面的「進行預測」或「登入頁面」時，對應的頁面組件就會被塞進這個位置。 -->

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router'; // 要「跳頁」👉 useRouter, 要「知道在哪一頁」👉 useRoute 
import { supabase } from '@/supabase';
import Profile from '@/views/profile.vue';

const router = useRouter();
const route = useRoute();
const isLoginedIn = ref(false); // 新增一個響應式狀態來跟蹤登入狀態

// 訂閱 Supabase 認證狀態的變更
let authListener = null;

onMounted(() =>{
  // 檢查當前 Session - 現在有沒有人登入
  supabase.auth.getSession().then(({ data: { session } }) => {
    isLoginedIn.value = !!session; // !!session 轉換為布林值 如果有人登入則為 true，否則為 false
  })

  // 訂閱狀態變更：當登入、登出、Token 刷新時都會觸發 登太久也會登出
  authListener = supabase.auth.onAuthStateChange((event, session) => {
    isLoginedIn.value = !!session;
      
    // 額外處理：當登出時，確保導航到登入頁
    if (event === 'SIGNED_OUT') {
        router.push('/login');
    }
  }).data.subscription  // 記憶體洩漏 (Memory Leak)：即便使用者離開了目前的頁面，監聽器依然在背景運作，佔用瀏覽器資源。邏輯衝突：如果你跳轉到了另一個不需要登入的頁面，背景的監聽器可能還在執行 router.push('/login')，導致使用者明明在看公開資訊，卻突然被踢回登入頁。
}) 

onUnmounted(() => {
  // 組件卸載時取消訂閱，避免記憶體洩漏
  if (authListener) {
    authListener.unsubscribe();
  }
})

// const handlelogout = async () => {
//   await supabase.auth.signOut(); // 1. 清除瀏覽器 local storage 或 cookie 裡的登入資訊 2.伺服器端結束該使用者的 session 資訊
//   // 由於我們在 onAuthStateChange 已經處理了導航，這裡可以省略 router.push（'/login'）
//   // 但保留也無妨
// }
</script>

<style>
/* 全域樣式 - 確保網頁沒有邊距，實現全螢幕效果 */
body {
  margin: 0;
  padding: 0;
  font-family: 'Arial', sans-serif;
  background-color: #f8f0e8 /* 輕微的背景色 */
}
  
/* App.vue 的 <style> 區塊現在可以放全域的基礎樣式 */
/* 您可以將之前 App.vue 中的 scoped 樣式移除或整合到這裡 */

#app-container {
  min-height: 100vh;        /* 撐滿整個視窗 */
  display: flex;
  flex-direction: column;
}

.page-content {
  flex: 1;                 /* 🔥 中間自動撐高 */
}

/* 右上區塊，按鈕 + 頭貼水平排列 */
.site-header {
  width: 100%;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between; /* 左右分開 */
  align-items: center;
  /* background-color: #fff; */
  /* border-bottom: 1px solid #ddd; */
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
}

.logo {
  font-size: 1.5rem;
  font-weight: 800;
  color: #4f8898;
  text-decoration: none;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-links {
  display: flex;
  gap: 8px;
  margin-right: 50px;
}

.nav-btn {
  padding: 6px 14px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 600;
  color: #e36f6f;
  background-color: #f5f0eb;
  transition: all 0.2s;
  font-size: 1.1rem;
}

.nav-btn:hover {
  background-color: #dcdcdc;
  color: #000;
}

/* --- Footer --- */
.site-footer {
  width: 100vw;                        /* 滿版背景 */
  margin-left: calc(50% - 50vw);       /* 修正左右空白 */
  background-color: #253e69;
  color: white;
  padding: 30px 20px;
  box-sizing: border-box;
  text-align: center;
  margin-top: auto;
}

.footer-content {
  max-width: 1200px;             /* 內容最大寬度 */
  margin: 0 auto;                /* 水平置中 */
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;                     /* 文字與連結間距 */
}

.footer-links a {
  color: white;                  /* 連結白色 */
  text-decoration: none;         /* 去掉底線 */
  margin: 0 10px;                /* 左右間距 */
  transition: color 0.3s;
}

.footer-links a:hover {
  color: #eda6c1;                /* 懸停變黃 */
}

.logout-btn {
  padding: 8px 16px;
  background: #8f6bb9; /* 紅色按鈕 */
  color: white;
  border: none;
  border-radius: 6px; /* 圓角 */
  font-size: 1rem;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: #4fa49d; /* 滑鼠懸停變亮 */
  transform: translateY(-2px); /* 微微上移 */
  box-shadow: 0 4px 8px rgba(0,0,0,0.2); /* 加陰影 */
}

.logout-btn:active {
  transform: translateY(0); /* 按下時回到原位 */
  box-shadow: none;
}
</style>


  
  