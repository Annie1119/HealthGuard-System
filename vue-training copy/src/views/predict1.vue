<template>
  <div class="predict-wrapper">
    <form class="predict-form" @submit.prevent="handleSubmit">

      <h2 class="form-title">Disease Risk Prediction</h2>

      <!-- 年齡 -->
      <div class="input-group">
        <label>Age:</label>
        <input type="number" v-model="age" placeholder="Enter your age" required min="1" max="120">
      </div>

      <!-- 性別 -->
      <div class="input-group">
        <label>Gender:</label>
        <select v-model="gender" required>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
          <option value="others">others</option>
        </select>
      </div>

      <!-- 病史 -->
      <div class="input-group">
        <label>Medical History & Additional Info:</label>
        <textarea 
          v-model="medical_history"
          placeholder="Enter any medical history, such as mild hypertension, no diabetes."
          rows="5"
          required>
        </textarea>
      </div>

      <!-- 提交按鈕 -->
      <button class="submit-btn" type="submit" :disabled="loading">  
        {{ loading ? 'Analyzing...' : 'Submit Analysis'}}
      </button> 
      <!-- when loading is true, the button will be set in the condition of disabled, users cannot click it(分析中的按鈕).-->
      <!-- disables(vue.js屬性綁定寫法)="loading" 完整屬性寫法 v-bind: disabled="loading" -->

    </form>
    <!-- 錯誤訊息顯示 -->
    <!-- <p v-if="errorMsg" class="message error-message">
      Error: {{ errorMsg }}
    </p>

    結果顯示
    <div v-if="riskReport" class="result-box"> 
      <h3 class="title">Prediction Result:</h3> -->
        <!-- <div :class="['risk-level', riskReport.risk_level.toLowerCase().replace('/', '-')]">
          <strong class="title">Risk Level:</strong> {{ riskReport.risk_level }}
        </div> -->
        <!-- <div class="risk-level-text" :class="riskLevelMap[riskReport.risk_level] || ''">
          Risk Level: {{ riskReport.risk_level }}
        </div> -->
        <!-- <div class="risk-level-text"
          :class="riskReport.risk_level_code === 'high' ? 'high-text' :
                  riskReport.risk_level_code === 'medium' ? 'medium-text' :
                  riskReport.risk_level_code === 'low' ? 'low-text' : ''">
          Risk Level: {{ riskReport.risk_level }}
        </div> -->

        <!-- <h3 class="title">Summary</h3>
        <p class="summary-text">{{ riskReport.summary }}</p>
        
        <h3 class="title">Suggestion</h3>
        <ul> -->
          <!-- <li v-for="(item, index) in riskReport.recommendations.split('\n').filter(r => r.trim() !== '')" :key="index" class="recommendation-text"> split('\n')過濾掉空行 filter(r => r.trim()前後兩端空白清除 -->
            <!-- {{ item }}
          </li>
        </ul>
    </div> -->
  </div>
</template>

<script setup>
// import { ref } from 'vue';
// import { supabase } from '@/supabase' // 引入 Supabase 客戶端

// // 預測數據
// const age = ref(30) // 創建響應式數據 自動更新
// const gender = ref('Male')
// const medical_history = ref('輕微高血壓，無糖尿病史')

// // 結果和狀態
// const riskReport = ref(null)
// const loading=ref(false)
// const errorMsg=ref(null)

// const riskLevelMap = {
//         '高': 'high-text',
//         '中': 'medium-text',
//         '低': 'low-text',
//         'High': 'high-text',
//         'Medium': 'medium-text',
//         'Low': 'low-text'
//       }

// // 後端 FastAPI URL
// const BACKEND_URL = 'http://localhost:8000'

// // 處理表單提交
// const handleSubmit = async () => { 
//   riskReport.value = null
//   errorMsg.value = null
//   loading.value = true // 開始加載分析，所以不能按下按鈕
// // async 不同步的意思 不會立即反回結果 會執行一些需要等待的操作

//   try {
//     // 1. 獲取當前 Supabase Session（這是關鍵！）
//     const {data: {session}, error: sessionError} = await supabase.auth.getSession() // await 暫定目前不同步的執行

//     if( sessionError || !session ){
//       // 如果沒有 Session，直接報錯
//       throw new Error("Please log in first, your session is invalid or has expired.")
//     }
//   // 取得 JWT Token 
//     const jwtToken = session.access_token
  
//   // 2.準備請求數據
//   const predictionData = {
//     age: age.value,
//     gender: gender.value,
//     medical_history: medical_history.value
//   }
  
//   // 3. 等待發送post請求到FastAPI的predict端點
//   const response = await fetch(`${BACKEND_URL}/predict`, { 
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json',
//       // 攜帶 JWT Token 進行身份驗證
//       'Authorization': `Bearer ${jwtToken}`
//     },
//     body: JSON.stringify(predictionData)
//   }) 

//   // 4. 處理 HTTP 響應
//   if (!response.ok) {
//     const errorData = await response.json()
//     //後端返回的 HTTPException 錯誤（例如"無效或過期的Token"）
//     throw new Error(errorData.detail || 'API request failed. Please check the backend logs.');
//   }

//   // 5. 成功獲取報告
//   const data = await response.json()
//   riskReport.value = data

//   } catch (error) {
//     // 捕獲並顯示錯誤信息
//     console.error('Prediction error:', error)
//     errorMsg.value = error.message || 'An unknown error occurred'
//   } finally {
//     loading.value = false // 無論成功或失敗，都結束加載狀態
//   }
// }
// // 整個 try...catch...finally 結構確保了以下可靠的執行流程：
// // try： 執行所有主邏輯（獲取 Session、發送 API 請求）。
// // 如果成功： 執行完 try 後跳過 catch，直接執行 finally。
// // 如果失敗（拋出錯誤）： try 立即停止執行，跳轉到 catch 區塊處理錯誤，然後執行 finally。

import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/supabase'

const router = useRouter()

// 輸入資料
const age = ref(30)
const gender = ref('Male')
const medical_history = ref('')

// 狀態
const loading = ref(false)
const errorMsg = ref(null)

// 後端 URL
const BACKEND_URL = 'http://localhost:8000'

// 提交表單
const handleSubmit = async () => { 
  errorMsg.value = null
  loading.value = true

  try {
    // 1. 取得 Supabase Session
    const { data: { session }, error: sessionError } = await supabase.auth.getSession()
    if (sessionError || !session) throw new Error("Please log in first, your session is invalid or has expired.")

    const jwtToken = session.access_token

    // 2. 準備預測資料
    const predictionData = {
      age: age.value,
      gender: gender.value,
      medical_history: medical_history.value
    }

    // 3. 發送 POST 到 FastAPI /predict
    const response = await fetch(`${BACKEND_URL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwtToken}`
      },
      body: JSON.stringify(predictionData)
    })

    if (!response.ok) {
      let errorText;
      try {
        const errorData = await response.json()
        errorText = errorData.detail || JSON.stringify(errorData)
      } catch {
        errorText = await response.text()
      }
      throw new Error(errorText || 'API request failed.')
    }

    const data = await response.json()

    // 已經在後端儲存到supabase了 前端不需要再做一次 否則會產出兩份一模一樣的報告
    // // 4. 存到 Supabase risk_reports
    // const { error: insertError } = await supabase
    //   .from('risk_reports')
    //   .insert([
    //     {
    //       user_id: session.user.id,
    //       input_data: predictionData,
    //       llm_report: data
    //     }
    //   ])

    // if (insertError) throw insertError

    // 5. 跳轉到 history 頁面
    router.push('/history')

  } catch (error) {
    console.error('Prediction error:', error)
    errorMsg.value = error.message || 'An unknown error occurred'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 外層置中 */
.predict-wrapper {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 120px;
}

/* 白色卡片 */
.predict-form {
  width: 480px;
  background: white;
  padding: 30px 35px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.12);
}

/* 標題 */
.form-title {
  font-size: 1.8rem;
  font-weight: 700;
  text-align: center;
  margin-bottom: 25px;
  color: #333;
}

.input-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 18px;
}

.input-group label {
  font-size: 1.1rem;
  color: #333;
}

input,
select,
textarea {
  margin-top: 6px;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 1.1rem;
  transition: border-color 0.3s;
}

input:focus,
select:focus,
textarea:focus {
  border-color: #1a73e8;
  outline: none;
}

/* 藍色按鈕 */
.submit-btn {
  width: 100%;
  padding: 15px;
  background: #1a73e8;
  border: none;
  color: white;
  font-size: 1.1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.submit-btn:hover {
  background: #135abe;
}

/* 結果框 */
.result-box {
  margin-top: 20px;
  background: #eef5ff;
  padding: 15px;
  border-radius: 8px;
}

.risk-level {
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 10px;
  padding: 8px;
  border-radius: 6px;
  /* color: rgb(34, 85, 162); */
  text-align: center;
}
/* 只改文字顏色 */
.high-text {
  color: #e53935; /* 紅色 */
}

.medium-text {
  color: #fab70d; /* 黃色 */
}

.low-text {
  color: #43a047; /* 綠色 */
}
.risk-level-text {
  font-size: 1.2rem;
  font-weight: bold;
  margin-bottom: 10px;
  text-align: center;
}
/* .risk-level.髙 {
  background-color: #e53935; 
}
.risk-level.中 {
  background-color: #fbc02d; 
}
.risk-level.低 {
  background-color: #43a047;
}
.risk-level.高中 {
  background-color: #ee782f; 
}
.risk-level.中低 {
  background-color: #3f98c5; 
} */
.title {
  color: purple;     
  font-weight: bold; 
}
.summary-text {
  color: #000000;
}
.recommendation-text {
  color: #000000; 
}
</style>

