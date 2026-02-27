<template>
  <div class="history-wrapper">
    <h2 class="page-title">Your Prediction History</h2>

    <div class="history-toolbar">
      <input type="date" v-model="startDate" />
      <input type="date" v-model="endDate" />

      <!-- <button class="search-btn" @click="filterByDate">🔍</button> -->
      <button class="overall-btn" @click="handleOpenOverallDetail">Overall Result</button>
    </div>

    <div v-if="loading" class="loading-overlay">Loading...</div>
    <div v-if="errorMsg" class="message error-message">{{ errorMsg }}</div>

    <div v-if="!loading && (!displayedReports || displayedReports.length === 0)" class="no-history">
      No history yet. Go make your first prediction!
    </div>

    <div v-for="riskReport in displayedReports" :key="riskReport.id" class="report-card">
      <button class="graph-btn" @click="openSingleGraph(riskReport)">Graph</button>

      <p><strong>Date:</strong> {{ formatDate(riskReport.created_at) }}</p>
      <p><strong>Age:</strong> {{ riskReport.input_data.age }}</p>
      <p><strong>Gender:</strong> {{ riskReport.input_data.gender }}</p>
      <p><strong>Medical History:</strong> {{ riskReport.input_data.medical_history }}</p>

      <h3 class="title">
        Possible Diseases 
        <small class="risk-guide">
          (<span class="high-text"> >60% High Risk</span> | 
          <span class="medium-text">30~60% Medium Risk</span> )
        </small>
      </h3>

      <ul>
        <li v-for="(disease,i) in riskReport.merged_diseases.filter(d => d?.probability >= 30)" :key="i"
            :class="{
              'high-text': disease.probability >= 60,
              'medium-text': disease.probability >= 30 && disease.probability < 60
            }">
          {{ disease.name }} — {{ disease.probability }}%
        </li>
      </ul>

      <h3 class="title">Summary</h3>
      <p class="summary-text">{{ riskReport.llm_report.summary }}</p>

      <h3 class="title">Recommendations</h3>
      <ul>
        <li v-for="(item,i) in formatRecommendations(riskReport.llm_report.recommendations)" :key="i" class="recommendation-text">
          {{ item }}
        </li>
      </ul>
    </div>

    <div v-for="(report,index) in singleModals" :key="'single-'+index" class="modal"
      :ref="el => singleModalRefs[index] = el"
      @mousedown="startDrag($event,'single',index)"
      :style="{ width: report.width+'px', height: report.height+'px', left: report.left+'px', top: report.top+'px', zIndex: report.zIndex }">
      
      <button class="close-btn" @click="closeSingleGraph(index)">✕</button>
      <h3 style="color: #000000; text-align: center; font-size: 1.2rem; font-weight: 600;">
          Report Graph
      </h3>

      <div class="canvas-wrapper">
        <canvas :ref="el => report.canvasRef = el"></canvas>
      </div>

      <p class="risk-legend">
        <span class="high-text">>60% High Risk </span><span style="color:black;">| </span> 
        <span class="medium-text">30~60% Medium Risk </span><span style="color:black;">| </span> 
        <span class="low-text"><30% Low Risk</span>
      </p>

      <div class="resizer" @mousedown.prevent="startResize($event,'single',index)"></div>
    </div>

    <div v-for="(detail, index) in overallDetails" :key="'overall-' + index" class="modal"
      :ref="el => overallModalRefs[index] = el"
      @mousedown="startDrag($event, 'overall', index)"
      :style="{ width: detail.width + 'px', height: detail.height + 'px', left: detail.left + 'px', top: detail.top + 'px', zIndex: detail.zIndex }">

      <button class="close-btn" @click="closeOverallDetail(index)">✕</button>
      <h3 class="modal-header">Health Analysis Insight</h3>

      <div class="overall-content" style="overflow:auto; flex:1; padding:15px;">
        <div v-for="(disease, i) in detail.data.diseases" :key="i" class="disease-card">
          <h4 class="disease-name-title">{{ disease.name }}</h4>
          
          <div class="info-group">
            <label>💡 Why it occurs (Cause):</label>
            <p>{{ disease.cause }}</p>
          </div>

          <div class="info-group">
            <label>🚀 Why it matters (Importance):</label>
            <p>{{ disease.importance }}</p>
          </div>
          <hr class="divider" />
        </div>

        <div v-if="detail.data.general_note" class="note-section">
          <strong>Note:</strong> {{ detail.data.general_note }}
        </div>
      </div>

      <div class="resizer" @mousedown.prevent="startResize($event, 'overall', index)"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { supabase } from '@/supabase'
import Chart from 'chart.js/auto'
import axios from 'axios'
import { ref, onMounted, nextTick, watch } from 'vue'

const BACKEND_URL = 'http://localhost:8000'

/* ---------------- Data ---------------- */
const riskReports = ref([])
const displayedReports = ref([])
const loading = ref(false)
const errorMsg = ref(null)

const startDate = ref(null)
const endDate = ref(null)

/* ---------------- Modal 狀態 ---------------- */
const singleModals = ref([])
const singleModalRefs = ref([])
const overallDetails = ref([]) // 儲存詳細分析內容
const overallModalRefs = ref([])

let currentZIndex = 1000
const getNextZIndex = () => ++currentZIndex

/* ---------------- 合併邏輯 ---------------- */
const mergeReports = (report) => {
  const llm = report.llm_report?.possible_diseases || []
  const rule = report.rule_report?.possible_diseases || []
  const map = {}
  llm.forEach(d => map[d.name] = { name: d.name, probability: d.probability })
  rule.forEach(d => {
    if (map[d.name]) map[d.name].probability = Math.max(map[d.name].probability, d.probability)
    else map[d.name] = { name: d.name, probability: d.probability }
  })
  return Object.values(map)
}

/* ---------------- 功能函數 ---------------- */
const fetchHistory = async () => {
  loading.value = true
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if(!session) return
    const { data, error } = await supabase
      .from('risk_reports')
      .select('*')
      .eq('user_id', session.user.id)
      .order('created_at',{ascending:false})
    if(error) throw error
    riskReports.value = (data || []).map(r => ({ ...r, merged_diseases: mergeReports(r) }))
    displayedReports.value = riskReports.value
  } catch(err) {
    errorMsg.value = "Failed to fetch history"
  } finally { loading.value = false }
}

watch([startDate, endDate], () => {
  console.log("日期變動，自動執行過濾...");
  filterByDate();
})

const filterByDate = () => {
  if (!startDate.value && !endDate.value) {
    displayedReports.value = riskReports.value;
    return;
  }

  displayedReports.value = riskReports.value.filter(r => {
    // 取得報告的日期部分 "YYYY-MM-DD"
    const rDate = new Date(r.created_at).toISOString().split('T')[0];
    
    const start = startDate.value; // HTML date input 格式也是 "YYYY-MM-DD"
    const end = endDate.value;

    if (start && rDate < start) return false;
    if (end && rDate > end) return false;
    return true;
  })
}

/* ---------------- 單筆圖表 ---------------- */
const openSingleGraph = async report => {
  const width = 500, height = 350
  const modalObj = {
    report, width, height, zIndex: getNextZIndex(),
    left: (window.innerWidth-width)/2, top: (window.innerHeight-height)/2,
    canvasRef:null, chartInstance:null, aspectRatio: width/height
  }
  singleModals.value.push(modalObj)
  await nextTick()
  const ctx = modalObj.canvasRef.getContext('2d')
  const chartData = modalObj.report.merged_diseases
  modalObj.chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: chartData.map(d => d.name),
      datasets: [{
        label: "Probability (%)",
        data: chartData.map(d => d.probability),
        backgroundColor: chartData.map(d => getSeverityColor(d.probability))
      }]
    },
    options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 100 } } }
  })
}

/* ---------------- 綜合分析 (字串比對強效版) ---------------- */
const handleOpenOverallDetail = async () => {
  // 這裡已經不需要再呼叫 filterByDate()，因為 watch 已經幫你做好了
  if (displayedReports.value.length === 0) {
    errorMsg.value = "Selected range has no reports to analyze.";
    return;
  }

  loading.value = true;
  errorMsg.value = null;

  try {
    const { data: { session } } = await supabase.auth.getSession();
    
    // 收集畫面上顯示的報告
    const diseaseMap = {};
    displayedReports.value.forEach(report => {
      report.merged_diseases.forEach(d => {
        if (d.probability >= 30) {
          if (!diseaseMap[d.name] || d.probability > diseaseMap[d.name].probability) {
            diseaseMap[d.name] = d;
          }
        }
      })
    })

    const payload = Object.values(diseaseMap);

    const response = await axios.post(`${BACKEND_URL}/overall-insight`, payload, {
      headers: { Authorization: `Bearer ${session.access_token}` }
    })

    overallDetails.value.push({
      width: 650, height: 550,
      left: (window.innerWidth - 650) / 2,
      top: (window.innerHeight - 550) / 2,
      zIndex: getNextZIndex(),
      aspectRatio: 650 / 550,
      data: response.data 
    });

    await nextTick();
  } catch (err) {
    errorMsg.value = "Analysis failed.";
  } finally {
    loading.value = false;
  }
}

const closeSingleGraph = i => singleModals.value.splice(i,1)
const closeOverallDetail = i => overallDetails.value.splice(i,1)

/* ---------------- 拖拉 & 縮放 ---------------- */
const startDrag = (e,type,index)=>{
  if(e.target.classList.contains('resizer')) return
  const list = type==='single' ? singleModals.value : overallDetails.value
  const item = list[index]
  const refs = type==='single' ? singleModalRefs.value : overallModalRefs.value
  item.zIndex = getNextZIndex()
  const modal = refs[index]
  dragInfo = { type, index, startX:e.clientX, startY:e.clientY, modal, origLeft:modal.offsetLeft, origTop:modal.offsetTop }
  window.addEventListener('mousemove',drag)
  window.addEventListener('mouseup',stopDrag)
}

const drag = e=>{
  if(!dragInfo) return
  const dx = e.clientX - dragInfo.startX
  const dy = e.clientY - dragInfo.startY
  const list = dragInfo.type==='single' ? singleModals.value : overallDetails.value
  list[dragInfo.index].left = dragInfo.origLeft + dx
  list[dragInfo.index].top = dragInfo.origTop + dy
}

const stopDrag = ()=>{ window.removeEventListener('mousemove',drag); window.removeEventListener('mouseup',stopDrag); dragInfo=null }

const startResize = (e,type,index)=>{
  const list = type==='single'?singleModals.value:overallDetails.value
  const modal = list[index]
  resizeInfo = { type, index, startX:e.clientX, startY:e.clientY, startWidth:modal.width, startHeight:modal.height, aspectRatio:modal.aspectRatio }
  window.addEventListener('mousemove',resize)
  window.addEventListener('mouseup',stopResize)
}

const resize = async e=>{
  if(!resizeInfo) return
  const list = resizeInfo.type==='single'?singleModals.value:overallDetails.value
  const modal = list[resizeInfo.index]
  modal.width = Math.max(350, resizeInfo.startWidth + (e.clientX - resizeInfo.startX))
  modal.height = modal.width / resizeInfo.aspectRatio
  await nextTick()
  if(modal.chartInstance) modal.chartInstance.resize()
}

const stopResize = ()=>{ window.removeEventListener('mousemove',resize); window.removeEventListener('mouseup',stopResize); resizeInfo=null }

const formatDate = (t) => new Date(t).toLocaleDateString('en-US',{year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})
const formatRecommendations = (r) => Array.isArray(r) ? r : []
const getSeverityColor = (prob) => prob >= 60 ? '#e53935' : (prob >= 30 ? '#fab70d' : '#43a047')

onMounted(fetchHistory)
</script>

<style scoped>
.history-wrapper { max-width:1000px; margin:0 auto; padding:50px 20px; position:relative; }
.page-title { font-size:2rem; font-weight:bold; text-align:center; margin-bottom:30px; color:#182b86; }
.history-toolbar { display:flex; justify-content:center; gap:10px; margin-bottom:20px; }
.overall-btn { padding:6px 12px; border-radius:6px; border:none; background:#4fa3ff; color:white; cursor:pointer; font-weight:bold; }
.overall-btn:hover { background:#2f7bdf; }

.report-card { background:#eef5ff; padding:20px; border-radius:12px; margin-bottom:20px; color:#000; position:relative; }
.graph-btn { position:absolute; top:12px; right:12px; background:#4fa3ff; color:white; border:none; border-radius:6px; padding:6px 10px; cursor:pointer; }
.title { color:purple; font-weight:bold; margin-top:10px; margin-bottom:5px; border-left: 4px solid purple; padding-left: 8px; }

/* Modal 通用樣式 */
.modal { position:fixed; background:white; border-radius:12px; padding:16px; cursor:move; display:flex; flex-direction:column; box-shadow: 0 10px 30px rgba(0,0,0,0.2); border: 1px solid #ddd; }
.close-btn { position:absolute; top:10px; right:10px; background:transparent; border:none; font-size:1.5rem; cursor:pointer; }
.canvas-wrapper { position:relative; width:100%; flex: 1; min-height: 0; }
.resizer { width:12px; height:12px; background:#4fa3ff; position:absolute; right:0; bottom:0; cursor:se-resize; border-radius:50%; }

/* 綜合報告內容樣式 */
.modal-header { text-align: center; color: #1a237e; border-bottom: 2px solid #e8eaf6; padding-bottom: 10px; margin-bottom: 15px; }
.disease-card { background: linear-gradient(135deg, #ffffff 0%, #f0f4ff 100%); border-radius: 12px; padding: 15px; margin-bottom: 15px; border-left: 6px solid #3949ab; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
.disease-name-title { font-size: 1.15rem; font-weight: 800; color: #1a237e; margin-bottom: 8px; }
.info-group label { display: block; font-weight: bold; color: #5c6bc0; margin-bottom: 3px; }
.info-group p { margin: 0; font-size: 0.95rem; line-height: 1.6; color: #333; }
.note-section { background: #fffde7; padding: 12px; border-left: 4px solid #fbc02d; margin-top: 10px; font-size: 0.9rem; }

.loading-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; font-size: 32px; font-weight: bold; color: #a6a0f3; z-index: 9999; background: rgba(255,255,255,0.7); }
</style>