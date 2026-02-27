<template>
    <div class="input">
        <h2>輸入生物數據</h2>
        <!--紅血球（rbc）輸入-->
        <div class="input-group">
           <label for="rbc">紅血球 (RBC) [M/uL]:</label>
           <input id="rbc" type="number" step="0.1" v-model.number="formData.rbc" placeholder="例如: 5.5"/>
        </div>

        <!--白血球（wbc）輸入-->
        <div class="input-group">
           <label for="wbc">白血球 (WBC) [K/uL]:</label>
           <input 
            id="wbc" 
            type="number" 
            step="0.1" 
            v-model.number="formData.wbc" 
            placeholder="例如: 7.0" /> <!-- step 遞增遞減數值, placeholder=預設提示文字, v-model.number="formData.wbc" 綁訂做同步 number是type-->
        </div>

        <!--體溫（Temp）輸入-->
        <div class="input-group">
           <label for="temp">體溫 (Temp) [C]:</label>
           <input id="temp" 
           type="number" step="0.1" v-model.number="formData.temp" placeholder="例如: 37.0"/>
        </div>

        <!-- 按鈕可以觸發額外動作，但這裡主要依賴 watch 實時更新 -->
        <button @click="emitUpdate">更新數據並分析</button> <!-- @click 監聽點擊事件，觸發 emitUpdate 函式-->

    </div>
</template>

<script setup> // 每个 *.vue 文件最多可以包含一个 <script setup> (不包括一般的 <script>) 这个脚本块将被预处理为组件的 setup() 函数，这意味着它将为每一个组件实例都执行。<script setup> 中的顶层绑定都将自动暴露给模板
import{reactive, watch} from 'vue';

// 1. 定義 Props：接收父元件 App.vue 傳來的初始數據 
const props = defineProps({  // 常數不是變數定義了不能改
    initialData:{
        type:Object,
        required:true,
        default: () => ({ rbc: 5.5, wbc: 7.0, temp: 37.0})
    }
});

// 2. 定義 Emit：宣告這個元件可以向父元件發送'data-updated'事件
const emit = defineEmits(['data-updated']);

// 3. 內部狀態：使用 reactive 創建可編輯的表單數據
// 必須從 props 複製，以避免直接修改 props（這是 Vue 最佳實踐）
const formData = reactive({
    rbc: props.initialData.rbc,
    wbc: props.initialData.wbc,
    temp: props.initialData.temp
})

// 4. 定義 Emit 函式
const emitUpdate = () => {
    // 發送當前表單數據給父元件（App.vue）
    emit('data-updated', {...formData}) // ...展開運算子 把 formData 裡的所有屬性展開出來並傳出去

};

// 5. 監聽 Props 變化（如果 App.vue 改變了初始值，則同步更新表單）=> 接收數據確保接收的跟原本的是一致的 父->子（流入）
watch(() => props.initialData, (newVal) => {
    Object.assign(formData, newVal); //覆蓋
}, {deep: true}); // 深度監聽：監聽器不僅會檢測物件或陣列的引用地址，還會遞歸地遍歷該物件或陣列的所有巢狀屬性 淺層監聽器：只會檢測物件或陣列本身的引用地址是否發生變化

// 6. 實時監聽 formData 變化並 Emit（更即時的互動）=> 子->父（流出）發送本地數據，確保父元件數據更新
watch(formData, emitUpdate, {deep: true}); // 更新
</script>

<style scoped> /* scoped 樣式只會應用於當前元件，避免樣式衝突 */
.input-form { 
  padding: 20px;
  background-color: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
h2 {
  color: #333;
  border-bottom: 1px solid #ccc;
  padding-bottom: 10px;
  margin-bottom: 20px;
}
.input-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 15px;
}
label {
  font-weight: bold;
  margin-bottom: 5px;
  color: #555;
}
input[type="number"] { /* type 指的是 HTML <input> 的類型，在這裡是數字輸入框 */
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 16px;
  transition: border-color 0.3s; /* transition 屬性用來定義當元素的某些屬性發生變化時，這些變化應該如何過渡。這裡指定了 border-color 屬性在 0.3 秒內平滑過渡 */
}
input[type="number"]:focus { /* :focus 表示元素目前被選中或點擊（獲得焦點）*/
  border-color: #1a5a89;
  outline: none;
}
button {
  background-color: #1a5a89;
  color: white;
  padding: 10px 15px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s; 
  width: 100%;
  margin-top: 10px;
}
button:hover {  /*滑鼠移上去變色*/
  background-color: #14496d;
}
</style>
