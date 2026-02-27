<template>
  <div class="profile_pic-btn" v-if="userLoaded">
    <img :src="profilePicture || defaultProfilePicture" @click="toggle" />
  </div>

  <div v-if="open" class="overlay" @click="close"></div>

  <aside class="drawer" :class="{ open }" v-if="userLoaded">
    <div class="drawer-content">
      <h3 class="title">Profile</h3>

      <div v-if="!editMode">
        <div class="avatar-display">
           <img :src="profilePicture || defaultProfilePicture" class="preview" />
        </div>
        <p class="info"><strong>Username:</strong> {{ username }}</p>
        <p class="info"><strong>Email:</strong> {{ email }}</p>
        <p class="info"><strong>Password:</strong> ******</p>

        <div class="btn-row">
          <button class="edit" @click="editMode = true">Edit</button>
        </div>
      </div>

      <div v-else>
        <div class="profile-picture-upload">
          <label style="color: black;"><strong>Profile Picture:</strong></label>
          <input type="file" @change="handleFileUpload" accept="image/*" />
          <img :src="profilePicture || defaultProfilePicture" class="preview" />
        </div>

        <label class="info">Username
          <input v-model="usernameInput" />
        </label>

        <label class="info">Email
          <input v-model="emailInput" />
        </label>

        <label class="info">New Password
          <input type="password" v-model="passwordInput" placeholder="Leave blank to keep current" />
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
const currentUserId = ref(null);

const username = ref('');
const email = ref('');
const profilePicture = ref(''); 

// 已替換為你提供的 Flaticon 預設圖片連結
const defaultProfilePicture = 'https://cdn-icons-png.flaticon.com/512/1144/1144760.png';

const usernameInput = ref('');
const emailInput = ref('');
const passwordInput = ref('');

const toggle = () => (open.value = !open.value);
const close = () => { open.value = false; editMode.value = false; }

onMounted(async () => {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return;

  currentUserId.value = user.id;
  email.value = user.email;
  username.value = user.user_metadata?.display_name || '';

  // 從 profiles1 抓取資料
  const { data: profileData, error } = await supabase
    .from('profiles1')
    .select('avatar_data')
    .eq('id', user.id)
    .single();

  if (!error && profileData?.avatar_data) {
    profilePicture.value = profileData.avatar_data;
  }

  usernameInput.value = username.value;
  emailInput.value = email.value;
  userLoaded.value = true;
});

const handleFileUpload = async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  if (file.size > 5 * 1024 * 1024) {
    alert("The file is too large. Please select an image smaller than 5MB.");
    return;
  }

  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = (event) => {
    const img = new Image();
    img.src = event.target.result;
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const MAX_WIDTH = 200; 
      const scaleSize = MAX_WIDTH / img.width;
      canvas.width = MAX_WIDTH;
      canvas.height = img.height * scaleSize;

      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // 壓縮為 WebP
      const compressedBase64 = canvas.toDataURL('image/webp', 0.7);
      profilePicture.value = compressedBase64;
    };
  };
};

const save = async () => {
  try {
    // 這邊會更新儲存在 Supabase Auth Metadata 裡的顯示名稱和 Email，密碼則會更新到 Auth 系統
    const authUpdates = { data: { display_name: usernameInput.value } };
    if (emailInput.value !== email.value) authUpdates.email = emailInput.value;
    if (passwordInput.value) authUpdates.password = passwordInput.value;

    const { error: authError } = await supabase.auth.updateUser(authUpdates);
    if (authError) throw authError;

    // 更新 profiles1 資料表
    const { error: dbError } = await supabase
      .from('profiles1')
      .upsert({ 
        id: currentUserId.value, 
        avatar_data: profilePicture.value,
        display_name: usernameInput.value,
        email: emailInput.value
      });

    if (dbError) throw dbError;
    
    // 同步前端 UI 狀態
    username.value = usernameInput.value;
    email.value = emailInput.value;
    passwordInput.value = ''; // Clear password field for security
    editMode.value = false;
    alert("Profile updated!");
  } catch (err) {
    alert("Save failed: " + err.message);
  }
};

const cancel = () => {
  editMode.value = false;
  usernameInput.value = username.value;
  emailInput.value = email.value;
  passwordInput.value = '';
};

const logout = async () => {
  await supabase.auth.signOut();
  location.reload();
};
</script>

<style scoped>
/* 樣式保持一致 */
.profile_pic-btn { position: fixed; top: 12px; right: 12px; cursor: pointer; z-index: 1001; }
.profile_pic-btn img { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); background: #eee; }

.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 1000; }

.drawer { position: fixed; top: 0; right: 0; width: 360px; height: 100vh; background: white; padding: 20px;
  z-index: 1002; transform: translateX(100%); transition: transform 0.3s ease; display: flex; flex-direction: column; box-shadow: -4px 0 10px rgba(0,0,0,0.1); }
.drawer.open { transform: translateX(0); }
.drawer-content { flex: 1; overflow-y: auto; }

.title { font-weight: bold; font-size: 1.5rem; margin-bottom: 20px; color: #000; border-bottom: 2px solid #eee; padding-bottom: 10px; }
.info { font-weight: bold; font-size: 1.1rem; margin-bottom: 12px; color: #333; display: block; }
input { width: 100%; padding: 10px; margin-top: 6px; border-radius: 8px; border: 1px solid #ddd; }

.btn-row { display: flex; gap: 10px; margin-top: 25px; }
button { padding: 10px 16px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; }

button.edit { background: #945ee5; color: white; width: 100%; }
button.save { background: #56c5c5; color: white; flex: 1; }
button.cancel { background: #6ea4dd; color: white; flex: 1; }

.avatar-display { text-align: center; margin-bottom: 20px; }
.preview { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #f0f0f0; margin: 10px auto; display: block; background: #eee; }

.drawer-bottom { display: flex; gap: 12px; justify-content: flex-end; padding-top: 20px; border-top: 1px solid #eee; margin-top: 20px; }
button.logout { background: #4dbbce; color: white; }
button.close { background: #5792d9; color: white; }
.profile-picture-upload input[type="file"] {
  color: black;
  margin-top: 10px;
  margin-bottom: 10px;
}
</style>


