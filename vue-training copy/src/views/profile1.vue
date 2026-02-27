<template>
  <!-- 頭貼按鈕 -->
  <div class="profile_pic-btn" v-if="userLoaded">
    <img :src="profilePicture || defaultProfilePicture" @click="toggle" />
  </div>

  <!-- 遮罩 -->
  <div v-if="open" class="overlay" @click="close"></div>

  <!-- Drawer -->
  <aside class="drawer" :class="{ open }" v-if="userLoaded">
    <div class="drawer-content">
      <h3 class="title">Profile</h3>

      <div v-if="!editMode">
        <p class="info"><strong>Username:</strong> {{ username }}</p>
        <p class="info"><strong>Email:</strong> {{ email }}</p>
        <p class="info"><strong>Password:</strong> ******</p>

        <div class="btn-row">
          <button class="edit" @click="editMode = true">Edit</button>
        </div>
      </div>

      <div v-else>
        <div class="profile-picture-upload">
          <label><strong>Profile Picture:</strong></label>
          <input type="file" @change="uploadProfilePicture" />
          <img v-if="profilePicture" :src="profilePicture" class="preview" />
        </div>

        <label class="info">Username
          <input v-model="usernameInput" />
        </label>

        <label class="info">Email
          <input v-model="emailInput" />
        </label>

        <label class="info">New Password
          <input type="password" v-model="passwordInput" />
        </label>

        <div class="btn-row">
          <button class="save" @click="save">Save</button>
          <button class="cancel" @click="cancel">Cancel</button>
        </div>
      </div>
    </div>

    <div class="drawer-bottom">
      <button class="logout" @click="logout">Logout</button>
      <button class="close" @click="close">Close</button>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { supabase } from '../supabase';

const open = ref(false);
const editMode = ref(false);
const userLoaded = ref(false);

const username = ref('');
const email = ref('');
const profilePicture = ref('');
const defaultProfilePicture = 'https://ui-avatars.com/api/?background=000000&color=ffffff&size=128&name=User';

const usernameInput = ref('');
const emailInput = ref('');
const passwordInput = ref('');

const toggle = () => (open.value = !open.value);
const close = () => { open.value = false; editMode.value = false; }

onMounted(async () => {
  const { data } = await supabase.auth.getUser();
  const user = data.user;
  if (!user) return;

  username.value = user.user_metadata?.display_name || '';
  email.value = user.email;
  profilePicture.value = user.user_metadata?.profilePicture || '';

  usernameInput.value = username.value;
  emailInput.value = email.value;

  userLoaded.value = true;
});

const save = async () => {
  const updates = { 
    data: { 
      display_name: usernameInput.value, 
      profilePicture: profilePicture.value 
    } 
  };
  if (emailInput.value !== email.value) updates.email = emailInput.value;
  if (passwordInput.value) updates.password = passwordInput.value;

  const { error } = await supabase.auth.updateUser(updates);
  if (error) return alert(error.message);

  username.value = usernameInput.value;
  email.value = emailInput.value;
  passwordInput.value = '';
  editMode.value = false;
};

const cancel = () => {
  editMode.value = false;
  usernameInput.value = username.value;
  emailInput.value = email.value;
  passwordInput.value = '';
  profilePicture.value = profilePicture.value;
};

const uploadProfilePicture = async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const fileExt = file.name.split('.').pop();
  const fileName = `${Math.random().toString(36).substring(2)}.${fileExt}`;
  
  // 直接用 fileName 或加子資料夾，例如 avatars/
  const filePath = `avatars/${fileName}`; // 可選 avatars 資料夾

  // 上傳
  const { error: uploadError } = await supabase.storage
    .from('profile-picture')       // bucket 名稱
    .upload(filePath, file, { upsert: true });

  if (uploadError) return alert('Upload failed: ' + uploadError.message);

  // 取得公開 URL
  const { data } = supabase.storage
    .from('profile-picture')
    .getPublicUrl(filePath);

  profilePicture.value = data.publicUrl;
};

const logout = async () => {
  await supabase.auth.signOut();
  location.reload();
};
</script>

<style scoped>
.profile_pic-btn { position: fixed; top: 12px; right: 12px; cursor: pointer; z-index: 1001; }
.profile_pic-btn img { width: 40px; height: 40px; border-radius: 50%; }

.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 1000; }

.drawer { position: fixed; top: 0; right: 0; width: 360px; height: 100vh; background: white; padding: 20px;
  z-index: 1002; transform: translateX(100%); transition: transform 0.3s ease; display: flex; flex-direction: column; }
.drawer.open { transform: translateX(0); }
.drawer-content { flex: 1; overflow-y: auto; }

.title { font-weight: bold; font-size: 1.5rem; margin-bottom: 16px; color: #000000}
.info { font-weight: bold; font-size: 1.1rem; margin-bottom: 12px; color: #000000}
label.info { font-weight: bold; font-size: 1.1rem; }
input { width: 100%; padding: 8px; margin-top: 4px; border-radius: 6px; border: 1px solid #ccc; }

.btn-row { display: flex; gap: 8px; margin-top: 16px; }
button { padding: 8px 14px; border-radius: 6px; border: none; cursor: pointer; font-weight: bold; font-size: 1rem; }
button.edit { background: #945ee5; color: white; }
button.save { background: #56c5c5; color: white; }
button.cancel { background: #6ea4dd; color: white; }

.profile-picture-upload label strong { margin-bottom: 12px; font-weight: bold; font-size: 1.1rem; color: #000000}
.profile-picture-upload .preview { width: 80px; height: 80px; border-radius: 50%; margin-top: 6px; object-fit: cover; border: 2px solid #ccc; }

.drawer-bottom { display: flex; gap: 12px; justify-content: flex-end; padding-top: 12px; border-top: 1px solid #eee; }
button.logout, button.close { font-size: 1.1rem; padding: 10px 16px; font-weight: bold; }
button.logout { background: #4dbbce; color: white; }
button.close { background: #5792d9; color: white; }
</style>

<template>
  <div>
    < img :src="userAvatar" @click="isOpen = true" class="profile-btn" />

    <div v-if="isOpen" class="sidebar">
      <button @click="isOpen = false">關閉</button>
      <h2>個人設定</h2>
      < img :src="userAvatar" class="large-avatar" />
      
      <input type="file" @change="uploadToDatabase" accept="image/*" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { supabase } from './supabase'; // 你的 supabase 設定

const isOpen = ref(false);
const userAvatar = ref('default-avatar.png'); // 初始預設圖

const uploadToDatabase = async (event) => {
  const file = event.target.files[0];
  const reader = new FileReader();

  reader.onloadend = async () => {
    const base64String = reader.result; // 將圖片轉為字串
    
    // 直接存入 Supabase 資料表，不經由 Bucket
    const { error } = await supabase
      .from('profiles')
      .update({ avatar_data: base64String }) // 假設你的欄位叫 avatar_data
      .eq('id', '使用者ID');

    if (!error) userAvatar.value = base64String;
  };
  reader.readAsDataURL(file);
};

const uploadToDatabase = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  // 1. 限制原始檔案大小（例如超過 5MB 直接拒絕，節省瀏覽器效能）
  if (file.size > 5 * 1024 * 1024) {
    alert("檔案太大了，請選擇小於 5MB 的圖片");
    return;
  }

  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = (e) => {
    const img = new Image();
    img.src = e.target.result;
    img.onload = async () => {
      // 2. 使用 Canvas 進行壓縮
      const canvas = document.createElement('canvas');
      const MAX_WIDTH = 200; // 設定頭貼最大寬度
      const scaleSize = MAX_WIDTH / img.width;
      canvas.width = MAX_WIDTH;
      canvas.height = img.height * scaleSize;

      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // 3. 轉為 WebP 格式（體積最小）並設定品質為 0.7
      const compressedBase64 = canvas.toDataURL('image/webp', 0.7);

      // 4. 存入 Supabase
      const { error } = await supabase
        .from('profiles')
        .update({ avatar_data: compressedBase64 })
        .eq('id', userId); // 替換為實際的 User ID

      if (!error) {
        userAvatar.value = compressedBase64;
        alert("頭貼更新成功！");
      } else {
        console.error("更新失敗:", error);
      }
    };
  };
};
</script>

<style scoped>
.profile-btn { width: 40px; height: 40px; border-radius: 50%; cursor: pointer; position: fixed; top: 10px; right: 10px; }
.sidebar { position: fixed; right: 0; top: 0; width: 300px; height: 100%; background: white; box-shadow: -2px 0 5px rgba(0,0,0,0.1); padding: 20px; z-index: 100; }
.large-avatar { width: 150px; height: 150px; border-radius: 50%; display: block; margin: 20px auto; }
</style>

