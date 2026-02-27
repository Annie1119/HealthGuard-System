<template> <!-- vue 裡面放html的區塊 -->
    <div class="result-display">
        <h2>分析結果與風險評估</h2>

    <!-- 顯示核心數據 -->
     <div class="data-summary">
        <p>紅血球 (RBC):<strong>{{currentData.rbc}} M/uL</strong></p>
        <p>白血球 (WBC):<strong>{{currentData.wbc}} K/uL</strong></p>
        <p>體溫 (Temp):<strong>{{currentData.temp}} C</strong></p>
     </div>
    
    <!--計算與顯示衍生指標 -->
    <div class="metrics">
        <h3>衍生指標</h3>
        <p>RBC/WBC 比率：
            <span :class="{'highlight-ratio':isRatioAbnormal}">
                {{ rbcWbcRatio.toFixed(2)}}
                ({{ isRatioAbnormal ? '異常風險':'正常範圍'}}) 
            </span>
        </p>
        <p>體溫異常度：
            <span>
                {{tempDeviation.toFixed(2)}} C
            </span>
        </p>
    </div>

    <!--顯示最終風險評估結果-->
    <div class="risk-assessment">
        <h3>整體風險評估</h3>
        <div :class="['risk-box', riskLevelClass]">
            {{riskLevelText}}
        </div>

        <p class="suggestion">{{ riskSuggestion }} </p>
    </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'; 
const props = defineProps({
    currentData: {
        type: Object,
        required: true,
    }
});

// 緩存 (Caching)ﾠ只要計算屬性所依賴的響應式數據沒有發生變化，再次訪問這個計算屬性時，它會立即返回上一次的計算結果，而不會重新執行函式。這提供了極佳的性能優化，避免了不必要的昂貴計算。
// 1. 計算 RBC/WBC 比率  
const rbcWbcRatio = computed(() => { 
    const {rbc, wbc} = props.currentData;
    if (wbc === 0) return 0; // 避免除以零 ===:是否完全嚴格相等
    return rbc / wbc;   
});

// 2. 判斷 RBC/WBC 比率是否異常 (簡易邏輯: 標準比例約 0.5~0.8)
const isRatioAbnormal = computed(() => {
    const ratio = rbcWbcRatio.value;
    return ratio < 0.4 || ratio > 1.0; // 只要低於0.4或高於1.0就return true
});

// 3. 計算體溫異常度 (以 37.0C 為準)
const tempDeviation = computed(() => {
    return Math.abs(props.currentData.temp - 37.0); // Math.abs() 絕對值
});

// 4. 根據風險等級顯示文字
const riskLevelText = computed(() => {
    const {wbc, temp} = props.currentData;

    // 判斷發燒/高風險體溫
    if (temp > 38.5) {
        return '緊急高風險:高燒警報';
    }

    // 判斷 WBC 異常（低於4.0 或高於 10.0）
    if (wbc < 4.0) {
        return '中度風險:WBC 過低，可能免疫力低下';
    }else if (wbc>10.0){
        return '中度風險:WBC 過高，可能存在感染或炎症';
    }

    // 判斷 RBC/WBC 比率異常
    if (isRatioAbnormal.value) {
        return '低風險:比率異常，建議複查';
    } 
    return '健康狀態：數據正常，風險極低';
}); 

// 5. 根據風險等級給予 CSS 類別（用於視覺化顏色）
const riskLevelClass = computed(() => {
    const text = riskLevelText.value;
        if (text.includes('緊急高風險')) return 'risk-high';
        if (text.includes('中度風險')) return 'risk-medium';
        return 'risk-low';
});

// 6. 提供建議
const riskSuggestion = computed(() => {
    const text = riskLevelText.value;
        if (text.includes('緊急高風險')) return '請立即諮詢醫生，並尋求專業醫療幫助。';
        if (text.includes('中度風險')) return '建議在專業醫護人員指導下進行進一步的血液檢查。';
        return '良好生活習慣，定期檢查。';
});
</script>

<style>
.result-display {
    padding: 20px;
    background-color: #f7f7f7;
    border: 1px solid #ddd;
    border-radius: 8px;
}
h2 {
    color: #333;
    border-bottom: 1px solid #ccc;
    padding-bottom: 10px;
    margin-bottom: 20px;
}
h3 {
    color: #1a5a89;
    margin-top: 20px;
    border-left: 4px solid #1a5a89;
    padding-left: 10px;
    font-size: 1.1em;
}
.data-summary p, .metrics p {
    margin: 8px 0;
    font-size: 1.05em;
    color: #555;
}
.metrics {
    margin-top: 25px;
    padding: 15px;
    background-color: #ffffff;
    border-radius: 6px;
    border: 1px solid #eee;
}
  .highlight-ratio {
    font-weight: bold;
    color: #e74c3c; /* 紅色高亮顯示異常比率 */
}
    .risk-assessment {
    margin-top: 30px;
}
.risk-box {
    padding: 15px;
    color: white;
    font-weight: bold;
    text-align: center;
    border-radius: 6px;
    margin-top: 10px;
    font-size: 1.2em;
}
.risk-low {
    background-color: #27ae60; /* 綠色 */
}
.risk-medium {
    background-color: #f39c12; /* 橙色 */
}
.risk-high {
    background-color: #e74c3c; /* 紅色 */
    animation: pulse 1.5s infinite; /* 增加閃爍效果 */ /* 套用動畫，1.5 秒循環一次 */
}
.suggestion {
    margin-top: 15px;
    padding: 10px;
    border-left: 5px solid #1a5a89;
    background-color: #e6f7ff;
    color: #1a5a89;
    font-style: italic;
}
/* 閃爍動畫 */
@keyframes pulse { /* 定義動畫名稱為 pulse */
    0% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.7); }  /* 開始時，紅色光暈半徑為 0，透明度 0.7 */
    70% { box-shadow: 0 0 0 10px rgba(231, 76, 60, 0); } /* 動畫進行到 70% 時，紅色光暈擴散到 10px 且透明消失 */
    100% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); }  /* 結束時回到原始狀態（無光暈） */
}
</style>

