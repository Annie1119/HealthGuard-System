<template>
  <div class="login-register-page">

    <header class="site-header">
          <router-link to="/" class="logo">
            HealthGuard🫀
          </router-link>
    </header>
        
    <div class="login-register-card">
        <h2 class="form-title">{{ (isRegistering ? 'Sign up' : 'Log In') }}</h2>
        
        <form @submit.prevent="handleSubmit"> <!-- prevent 攔截預設行為（頁面重新載入）執行handleSubmit -->
          <div class="input-group" v-if="isRegistering">
              <input 
                  id="username" 
                  type="text" 
                  v-model="username" 
                  placeholder="" 
                  required 
                  class="field-input"
              />
              <label for="username" class="field-label">Username</label>
          </div>  
          
          <div class="input-group">
                <input 
                    id="email" 
                    type="email" 
                    v-model="email" 
                    placeholder="" 
                    required
                    class="field-input"
                />
                <label for="email" class="field-label">Email</label>
                <!-- <span class="input-icon">👁️</span>  -->
            </div>

            <div class="input-group">
              <input 
                  id="password" 
                  :type="showPassword ? 'text' : 'password'" 	
                  v-model="password" 
                  placeholder="" 
                  required 
                  class="field-input"
              /> 
              
              <!--* 如果 showPassword 是 true → input 的type 會變成'text'（密碼可見）如果 showPassword 是 false → input的type 會變成 password'（密碼隱藏）'password' 是 HTML 的原生屬性值，表示文字被隱藏成點點。-->
              <label for="password" class="field-label">Password</label>
              <span class="input-icon" @click="showPassword = !showPassword"> <!-- 點擊時把 showPassword 的布林值反轉 -->
                {{ showPassword ? '🙈' : '👁️' }}
              </span>
            </div>

            <div v-if="errorMsg" class="message error-message">{{ errorMsg }}</div>
            <div v-if="successMsg" class="message success-message">{{ successMsg }}</div>

            <button type="submit" class="submit-btn">
                {{ (isRegistering ? 'Sign Up' : 'Log In') }}
            </button>
        </form>

        <div class="mode-link-bottom" @click="isRegistering = !isRegistering">
              {{ isRegistering ? 'Already have an account? Log In' : "Don't have an account? Sign Up" }}
        </div>

        <!-- <div class="predict-button-wrapper" style="margin-top: 20px; text-align: center;">
          <router-link to="/predict">
            <button class="submit-btn" style="background-color: #28a745; border: none;">
              Go to Predict Page
            </button>
          </router-link>
        </div> -->
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { supabase } from '@/supabase' // 引入 Supabase 客戶端

const router = useRouter();

// 響應式狀態
const username = ref('')
const email = ref('');
const isRegistering = ref('');
const password = ref(''); 
const showPassword = ref(false); // false = 密碼隱藏, true = 顯示密碼

// 錯誤訊息
const errorMsg = ref(null);
const successMsg = ref(null);

// 函式：處理登入
const handleLogin = async () => {
  errorMsg.value = null;
  successMsg.value = null;
  
  try {
    const { error } = await supabase.auth.signInWithPassword({
      email: email.value,
      password: password.value,
    })

    if (error) throw error
    router.push('/predict'); // 登入成功後跳轉到預測頁面

    }catch (error) {
      if (error.message.includes("Invalid login credentials")) {
      errorMsg.value = "Incorrect email or password";
    } else if (error.message.includes("User not confirmed")) {
      errorMsg.value = "Account not confirmed, please check your email";
    } else {
      errorMsg.value = "Login failed, please try again later";
    }
  }
}
  
// 函式：處理註冊 
const handleRegister = async () => {
  errorMsg.value = null;
  successMsg.value = null;

  try {
    const { error } = await supabase.auth.signUp({
      email: email.value,
      password: password.value,
      options: {
        data: {
          display_name: username.value, 
        }
      }
    })

    if (error) throw error

    // 註冊成功，提示使用檢查信箱進行驗證
    successMsg.value = 'Registration successful! Please check your email to confirm your account.';
    
    // 清空密碼欄位
    password.value = ''
  
    //自動切換回登入介面
    isRegistering.value = false;

    } catch (error) {
      errorMsg.value = error.message
    }
}

// 根據當前模式選擇執行登入或註冊
const handleSubmit = () => {
  if (isRegistering.value) {
    handleRegister();
  } else {
    handleLogin();
  }
}
</script>

<style scoped>
 .site-header {
  width: 100%;                   /* 讓 header 佔滿整個寬度 */
  position: fixed;                /* 固定在頁面頂部 */
  top: 0;                         /* 距離頂部 0 */
  left: 0;                        /* 距離左邊 0 */
  padding: 15px 20px;             /* 上下左右內距 */
  background-color: #ffffffcc;    /* 半透明白色背景 (#cc 是透明度) */
  display: flex;                  /* 使用彈性布局 */
  align-items: center;            /* 內容垂直置中 */
  z-index: 1000;                  /* 確保 header 在最上層 */
  box-shadow: 0 2px 6px rgba(0,0,0,0.1); /* 添加陰影 */
}

.logo {
  font-size: 1.5rem;              /* 字體大小 */
  font-weight: 800;               /* 字體加粗 */
  color: #4f8898;                 /* 字體顏色 */
  text-decoration: none; /* 移除底線 */
}

/* 頁面留出 header 高度 */
.home-page {
  padding-top: 60px;              /* 預留 60px 空間，避免 header 遮住內容 */
}

/* 外層容器，滿版白色背景 + 置中內容 */
.login-register-page {
  /* width: 100vw;      */         
  /* min-height: 100%; */
  position : fixed;           
  inset: 0;             /* top:0; right:0; bottom:0; left:0; 簡寫 */
  display: flex;              /* 使用 Flex 置中內容 */
  justify-content: center;    /* 水平置中 */
  align-items: flex-start;  /* 垂直置頂 */
  background-color: #f8f0e8;    /* 整個背景白色 */
  padding: 60px 20px 20px;    /* 預留 header 高度 + 左右內距 */
  box-sizing: border-box;
}

/* 卡片保持原本樣式 */
.login-register-card {
  margin-top: 150px;
  max-width: 330px;               
  width: 100%;
  /* padding: 30px 40px;             
  border-radius: 12px;            
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); 
  background-color: #f8f0e8;         */
  text-align: center;      
  transform: scale(1.2);       /* ⭐ 整體放大 15% */
  transform-origin: top center; /* 從上方中心點放大 */       
}

.form-title {
  font-size: 2.5rem;              /* 標題字體大小 */
  font-weight: 600;               /* 字體粗細 */
  color: #333;                     /* 顏色 */
  margin-bottom: 30px;            /* 標題下方間距 */
}

/* 輸入組容器 */
.input-group {
  margin-bottom: 20px;            /* 每個輸入框下方間距 */
  position: relative;             /* 方便定位 label 和 icon */
}

.field-input {
  width: 100%;                     /* 滿寬 */
  padding: 18px 15px 5px 15px;    /* 上內距大於下內距，給 label 留空間 */
  border: 1px solid #ccc;          /* 灰色邊框 */
  border-radius: 8px;              /* 圓角 */
  font-size: 1rem;                 /* 字體大小 */
  box-sizing: border-box;          /* 包含 padding 在內計算寬度 */
  transition: border-color 0.3s;   /* 邊框顏色變化加動畫 */
}

/* 聚焦時邊框變色 */
.field-input:focus {
  outline: none;                   /* 去掉預設藍色邊框 */
  border-color: #2196F3;           /* 聚焦時變藍色 */
}

/* Label 浮動效果 */
.field-label {
  position: absolute;              /* 絕對定位 */
  left: 15px;                      /* 距離左邊 15px */
  top: 5px;                        /* 距離頂部 5px */
  font-size: 0.8rem;               /* 小字體 */
  color: #999;                     /* 灰色 */
  pointer-events: none;            /* 點擊穿透到 input */
  transition: all 0.2s ease;       /* 動畫效果 */
}

/* 輸入框有值或聚焦時 label 浮上 */
.field-input:not(:placeholder-shown) + .field-label,  /* .field-label表示選擇緊接在 input 後面的 label 元素。效果：當 input 有值或聚焦時，label 會浮到上方、變小、變藍色，看起來像「漂浮標籤」的效果。*/
.field-input:focus + .field-label {
  top: 5px;                        /* label 上移 */
  font-size: 0.7rem;               /* label 變小 */
  color: #2196F3;                  /* label 變藍 */
}

/* 右側圖標（眼睛） */
.input-icon {
  position: absolute;              /* 絕對定位 */
  right: 15px;                     /* 距右 15px */
  top: 50%;                        /* 垂直置中 */
  transform: translateY(-50%);     /* 精確垂直置中 */
  color: #aaa;                     /* 灰色 */
  cursor: pointer;                 /* 滑鼠變成手指 */
  font-size: 1.1rem;               /* 字體大小 */
}

/* 提交按鈕 */
.submit-btn {
  width: 100%;                     /* 滿寬 */
  padding: 15px;                    /* 內距 */
  margin-top: 20px;                /* 上方間距 */
  border: none;                     /* 去掉邊框 */
  border-radius: 8px;               /* 圓角 */
  background-color: #2196F3;        /* 藍色背景 */
  color: white;                     /* 白字 */
  font-size: 1.1rem;               /* 字體大小 */
  font-weight: bold;               /* 粗體 */
  cursor: pointer;                 /* 滑鼠變成手指 */
  transition: background-color 0.3s; /* 背景變色動畫 */
}

.submit-btn:hover {                  /* :hover當滑鼠移到按鈕上時的狀態 */
  background-color: #1976D2;       /* 懸停變深藍 */
}

/* 底部切換連結 */
.mode-link-bottom {
  margin-top: 25px;                /* 上方間距 */
  font-size: 0.9rem;               /* 字體大小 */
  color: #666;                     /* 灰色 */
}

.link-text {
  color: #2196F3;                  /* 藍色字 */
  text-decoration: none;           /* 去掉底線 */
  font-weight: bold;               /* 粗體 */
  cursor: pointer;                 /* 滑鼠手指 */
}

.link-text:hover {
  text-decoration: underline;      /* 懸停加底線 */
}

/* 錯誤/成功訊息 */
.message {
  padding: 10px;                    /* 內距 */
  border-radius: 5px;               /* 圓角 */
  margin-bottom: 15px;             /* 下方間距 */
  text-align: left;                /* 左對齊 */
  font-size: 0.9rem;               /* 字體大小 */
}

.error-message {
  background-color: #fce4e4;       /* 淺紅背景 */
  color: #cc0033;                  /* 深紅文字 */
  border: 1px solid #cc0033;       /* 邊框紅色 */
}

.success-message {
  background-color: #e6ffe6;       /* 淺綠背景 */
  color: #008000;                  /* 綠色文字 */
  border: 1px solid #008000;       /* 綠色邊框 */
}

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background: white;   
  overflow: hidden;   /* ✅ 鎖住整個畫面，不能滑 */  
}

</style>

