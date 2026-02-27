<template>
  <div class="predict-wrapper">
    <div class="predict-card">
      <h2 class="form-title">Disease Risk Prediction</h2>

      <div class="grid">
        <div class="input-group">
          <label>Age</label>
          <input type="number" v-model="age" placeholder="Enter your age" min="1" max="120" />
        </div>

        <div class="input-group">
          <label>Gender</label>
          <select v-model="gender">
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
        </div>

        <div class="input-group">
          <label>Height (cm)</label>
          <input type="number" v-model="height" placeholder="170" />
        </div>

        <div class="input-group">
          <label>Weight (kg)</label>
          <input type="number" v-model="weight" placeholder="60" />
        </div>

        <div class="input-group">
          <label>Systolic BP</label>
          <input type="number" v-model="systolic_bp" placeholder="120" />
        </div>

        <div class="input-group">
          <label>Diastolic BP</label>
          <input type="number" v-model="diastolic_bp" placeholder="80" />
        </div>

        <div class="input-group">
          <label>Cholesterol (optional)</label>
          <input type="number" v-model="cholesterol" placeholder="Leave empty if unknown" />
        </div>

        <div class="input-group">
          <label>Glucose (optional)</label>
          <input type="number" v-model="glucose" placeholder="Leave empty if unknown" />
        </div>

        <div class="input-group">
          <label>Alcohol</label>
          <select v-model="alcohol">
            <option :value="0">No</option>
            <option :value="1">Yes</option>
          </select>
        </div>

        <div class="input-group">
          <label>Physical Activity</label>
          <select v-model="active">
            <option :value="0">No</option>
            <option :value="1">Yes</option>
          </select>
        </div>

        <div class="input-group">
          <label>Smoking Status</label>
          <select v-model="smoking_status">
            <option value="never smoked">Never</option>
            <option value="formerly smoked">Former</option>
            <option value="smokes">Current</option>
            <option value="N/A">N/A</option>
          </select>
        </div>

        <div class="input-group">
          <label>Family History of Heart Disease</label>
          <select v-model="family_heart_disease">
            <option :value="0">No</option>
            <option :value="1">Yes</option>
          </select>
        </div>

        <div class="input-group">
          <label>Stress Level</label>
          <select v-model="stress_level">
            <option :value="0">Low / None</option>
            <option :value="1">Moderate</option>
            <option :value="2">High</option>
          </select>
        </div>

        <div class="input-group">
          <label>High-fat / High-cholesterol Diet</label>
          <select v-model="high_fat_diet">
            <option :value="0">Rare / Never</option>
            <option :value="1">Sometimes</option>
            <option :value="2">Often</option>
          </select>
        </div>
      </div>

      <!-- ❤️ 心悸 + Additional Info Grid -->
      <div class="heart-section">
        <div class="heart-left">
          <label>Heart Palpitations / Arrhythmia Symptoms:</label>
          <div class="checkbox-grid">
            <label><input type="checkbox" v-model="symptoms.arrhythmia" value="rapid_heartbeat" /> Rapid heartbeat</label>
            <label><input type="checkbox" v-model="symptoms.arrhythmia" value="fluttering" /> Fluttering</label>
            <label><input type="checkbox" v-model="symptoms.arrhythmia" value="strong_heartbeat" /> Strong heartbeat</label>
            <label><input type="checkbox" v-model="symptoms.arrhythmia" value="irregular" /> Irregular / skipped beats</label>
            <label><input type="checkbox" v-model="symptoms.arrhythmia" value="chest_discomfort" /> Chest discomfort</label>
            <label><input type="checkbox" v-model="symptoms.arrhythmia" value="dizziness" /> Dizziness</label>
            <label><input type="checkbox" v-model="symptoms.arrhythmia" value="shortness_of_breath" /> Shortness of breath</label>
            <label><input type="checkbox" v-model="symptoms.arrhythmia" value="chest_tightness" /> Chest Tightness</label>
            <label><input type="checkbox" v-model="symptoms.arrhythmia" value="fatigue" /> Fatigue</label>
            <label><input type="checkbox" v-model="symptoms.arrhythmia" value="syncope" /> Fainting / Blackout</label>
          </div>
        </div>

        <div class="heart-right">
          <label>Symptoms / Additional Info</label>
          <textarea v-model="medical_history" rows="10" placeholder="Describe any symptoms or health info"></textarea>
        </div>
      </div>

      <button class="submit-btn" @click="handleSubmit" :disabled="loading">
        {{ loading ? 'Analyzing...' : 'Submit Analysis' }}
      </button>

      <p v-if="errorMsg" class="message error-message">{{ errorMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/supabase'

const router = useRouter()

// 基本資料
const age = ref(30)
const gender = ref('Male')

// 新增欄位
const systolic_bp = ref(120)
const diastolic_bp = ref(80)
const height = ref(170)
const weight = ref(60)
const cholesterol = ref(null)
const glucose = ref(null)

const alcohol = ref(0)
const active = ref(0)

const smoking_status = ref('never smoked')
const hypertensionValue = (systolic_bp.value > 140 || diastolic_bp.value > 90) ? 1 : 0
const family_heart_disease = ref(false)
const stress_level = ref(0)
const high_fat_diet = ref(0)
const symptoms = ref({ arrhythmia: [] })
const medical_history = ref('')

// 狀態
const loading = ref(false)
const errorMsg = ref(null)

// 後端 URL
const BACKEND_URL = 'http://localhost:8000'

const handleSubmit = async () => {
  loading.value = true
  errorMsg.value = null

  try {
    const { data: { session }, error: sessionError } = await supabase.auth.getSession()
    if (sessionError || !session) throw new Error("Please log in first.")

    const jwtToken = session.access_token

    const predictionData = {
      age: age.value,
      gender: gender.value,
      systolic_bp: systolic_bp.value,
      diastolic_bp: diastolic_bp.value,
      cholesterol: cholesterol.value || 0,
      glucose: glucose.value || 0,
      smoke: smoking_status.value === "smokes" ? 1 : 0,
      alcohol: alcohol.value,
      active: active.value,
      height: height.value,
      weight: weight.value,
      hypertension: hypertensionValue,
      family_heart_disease: family_heart_disease.value ? 1 : 0,
      stress_level: stress_level.value,
      high_fat_diet: high_fat_diet.value,
      symptoms: symptoms.value.arrhythmia,
      avg_glucose_level: glucose.value || 0,
      bmi: parseFloat((weight.value / ((height.value / 100) ** 2)).toFixed(1)),
      smoking_status: smoking_status.value,
      medical_history: medical_history.value
    }

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
/* =======================================
   頁面整體
======================================= */
.predict-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f3f7ff 0%, #ffffff 100%);
}

.predict-card {
  width: 900px;
  max-width: 95%;
  background: white;
  padding: 30px 40px;
  border-radius: 18px;
  box-shadow: 0 12px 30px rgba(0,0,0,0.15);
}

.form-title {
  font-size: 2rem;
  font-weight: 800;
  text-align: center;
  margin-bottom: 25px;
  color: #182b86;
}

/* =======================================
   Grid 兩欄排版
======================================= */
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px 22px;
}

/* =======================================
   單個輸入欄位
======================================= */
.input-group {
  display: flex;
  flex-direction: column;
}

.input-group label {
  font-size: 1rem;
  margin-bottom: 6px;
  color: #333;
}

input, select, textarea {
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #d3d3d3;
  font-size: 1rem;
  outline: none;
}

input:focus, select:focus, textarea:focus {
  border-color: #4fa3ff;
  box-shadow: 0 0 0 4px rgba(79,163,255,0.2);
}

/* =======================================
   心悸 + Additional Info
======================================= */
.heart-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  align-items: start; /* 對齊頂部 */
  margin-top: 24px;
}

.heart-left, .heart-right {
  display: flex;
  flex-direction: column;
}

.heart-left label, .heart-right label {
  font-weight: 500;
  margin-bottom: 10px;
  color: #333;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 20px;
}

.checkbox-grid label {
  display: flex;
  align-items: center;
  gap: 5px;
}

textarea {
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #d3d3d3;
  box-sizing: border-box;
}

/* =======================================
   按鈕
======================================= */
.submit-btn {
  width: 100%;
  padding: 14px;
  margin-top: 18px;
  background: #1a73e8;
  color: white;
  border: none;
  font-size: 1.1rem;
  border-radius: 12px;
  cursor: pointer;
}

.submit-btn:hover {
  background: #135abe;
}

/* =======================================
   錯誤訊息
======================================= */
.message.error-message {
  color: #e53935;
  margin-top: 10px;
  text-align: center;
}
</style>