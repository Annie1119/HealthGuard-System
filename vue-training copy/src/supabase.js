// src/supabase.js 設定supabase 和後端服務
import { createClient } from '@supabase/supabase-js'; // 建立 Supabase 客戶端的核心

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY; // 從環境變量中獲取 Supabase 的 URL 和匿名金鑰 允許匿名的使用者在設定的全限範圍內 與supabase互動

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
