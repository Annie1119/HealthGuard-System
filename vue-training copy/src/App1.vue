<!-- <script setup>
import HelloWorld from './components/HelloWorld.vue'
import TheWelcome from './components/TheWelcome.vue'
</script>

<template>
  <header>
    <img alt="Vue logo" class="logo" src="./assets/logo.svg" width="125" height="125" />

    <div class="wrapper">
      <HelloWorld msg="You did it!" />
    </div>
  </header>

  <main>
    <TheWelcome />
  </main>
</template>

<style scoped>
header {
  line-height: 1.5;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}
</style> -->

<template>
  <!-- 頂層模板只能有一個根元素，這裡是 div.container -->
  <div class="container">
    <h1>生物數據分析專案</h1>

    <!-- 子元件 1：數據輸入-->
    <DataInputForm 
      :initialData="bioData" 綁定屬性
      @data-updated="HandleDataUpdate" 監聽事件
    />

    <hr> <!--水平線-->

    <!-- 子元件 2：結果顯示（傳遞最新的 bioData）-->
    <ResultDisplay
      :currentData="bioData"
    />

  </div>
</template>

<script setup>
import { reactive } from 'vue';

// 引入子元件（請確保這兩個檔案已經在 src/components 資料夾中) 父元件是app.vue
import DataInputForm from './components/datainput.vue';
import ResultDisplay from './components/resultdisplay.vue';

// 數據狀態管理：使用 reactive 定義響應式對象
const bioData = reactive({ // 接收一個 JavaScript 物件（或陣列），並返回該物件的一個響應式代理 (Reactive Proxy)。這個 Proxy 物件能夠攔截對原始物件屬性的所有操作（讀取、寫入、刪除等） 
  rbc: 5.5, // 紅血球數值 (M/uL)
  wbc: 7.0, // 白血球數值 (K/uL)
  temp: 37.0 // 體溫 (C)
});

/**
 * 處理 DataInputForm 發送的數據更新事件
 * @param {Object} newData - 子元件傳遞回來的最新數據對象。
 */
const HandleDataUpdate = (newData) => { // HandleDataUpdate 接收子元件 在發出 data-updated 事件時 附帶傳遞過來的最新數據對象 
  // object.assign 將 newData 的所有屬性合併到 bioData 中，觸發響應式更新
  Object.assign(bioData, newData); // 把 newData 裡的所有屬性展開出來並傳給 bioData
  // console.log（'App.vue 接收到更新：'，bioData）；// 可以在開發者工具中查看數據是否正確更新
};

</script>

<style scoped>
.container {
  /* 設定最大寬度並置中 */
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Arial', sans-serif; /* 使用清晰的字體 */
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  background-color: #f9f9f9;
}
h1 {
    text-align: center;
    color: #1a5a89;
    padding-bottom: 10px;
    border-bottom: 2px solid #1a5a89;
    margin-bottom: 20px;
}
hr {
    margin: 30px 0;
    border: 0;
    border-top: 1px solid #ddd;
}
</style>