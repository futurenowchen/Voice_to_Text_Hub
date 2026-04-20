import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# [系統參數設定]
st.set_page_config(page_title="戰術語音轉譯中樞", page_icon="🎙️", layout="centered")
st.title("語音文本提取系統 v3.0 (高能批次版)")
st.markdown("### 系統狀態：待命\n全格式解鎖，序列批次處理，強制錨定高配額戰術引擎。")

# [安全驗證與金鑰載入]
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.text_input("輸入 Gemini API Key 以解鎖系統", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # [戰場偵查] 獲取可用模型清單
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # [強勢校準邏輯] 不論路徑前綴，強制捕捉具備 500 RPD 的 3.1 Lite
        target_model = ""
        priorities = ["3.1-flash-lite", "3.1-flash", "2.5-flash", "1.5-flash"]
        
        for keyword in priorities:
            for m in available_models:
                if keyword in m:
                    target_model = m
                    break
            if target_model: break
            
        # 保底方案
        if not target_model and available_models:
            target_model = available_models[0]

        st.info(f"系統已鎖定戰術引擎：`{target_model}`")
        
        # [前端解鎖] 撤除 type 限制擊穿 iOS 沙盒，開啟 accept_multiple_files
        uploaded_files = st.file_uploader(
            "部署音訊檔 (全格式解鎖，可一次選取多個檔案)", 
            type=None, 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            # 包含 iOS 自動轉碼的 mp4
            SUPPORTED_EXTS = ['m4a', 'mp3', 'wav', 'aac', 'ogg', 'flac', 'mp4']
            valid_files = []
            
            # [前端防爆檢查] 過濾無效資產
            for f in uploaded_files:
                ext = f.name.split('.')[-1].lower()
                if ext in SUPPORTED_EXTS:
                    valid_files.append(f)
                else:
                    st.warning(f"⚠️ 攔截：已排除非預期格式 {f.name}")
            
            if valid_files and st.button(f"啟動批次轉譯協議 (共 {len(valid_files)} 個檔案)"):
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                total_files = len(valid_files)
                master_transcript = ""
                
                # [序列解析迴圈]
                for index, file in enumerate(valid_files):
                    status_text.text(f"正在提取 ({index+1}/{total_files})：{file.name} ...")
                    
                    try:
                        file_ext = file.name.split('.')[-1].lower()
                        # 步驟一：建立本地暫存檔
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
                            tmp_file.write(file.getvalue())
                            tmp_path = tmp_file.name
                        
                        # 步驟二：拋轉至 Gemini 雲端
                        audio_file = genai.upload_file(path=tmp_path)
                        
                        while audio_file.state.name == "PROCESSING":
                            time.sleep(1)
                            audio_file = genai.get_file(audio_file.name)
                            
                        # 步驟三：執行精確提取
                        model = genai.GenerativeModel(model_name=target_model)
                        prompt = "你是一個精確的逐字稿轉譯員。請分析此檔案內容，並完整轉換為繁體中文逐字稿。絕對不要添加任何額外的解釋、問候或總結。"
                        response = model.generate_content([prompt, audio_file])
                        
                        # [文本縫合]
                        master_transcript += f"### 【檔案：{file.name}】\n"
                        master_transcript += response.text.strip() + "\n\n---\n\n"
                        
                        # 步驟四：防爆清理
                        genai.delete_file(audio_file.name)
                        os.unlink(tmp_path)
                        
                        # 步驟五：速率控制 (Rate Limit Control)
                        progress_bar.progress((index + 1) / total_files)
                        if index < total_files - 1:
                            time.sleep(2) # 強制冷卻，避免撞擊 RPM 紅線
                            
                    except Exception as e:
                        st.error(f"檔案 {file.name} 解析失敗：{str(e)}")
                        master_transcript += f"### 【檔案：{file.name}】\n[系統錯誤：無法解析此檔案]\n\n---\n\n"

                # [輸出戰術成果]
                status_text.text("序列轉譯完成。")
                st.success(f"已成功縫合 {len(valid_files)} 個語音資產。")
                
                st.text_area("整合純文字文本", master_transcript, height=400)
                
                st.download_button(
                    label="下載整合文本 (.txt)",
                    data=master_transcript,
                    file_name=f"Batch_Transcript_{int(time.time())}.txt",
                    mime="text/plain"
                )

    except Exception as e:
        st.error(f"系統錯誤：{str(e)}")
        with st.expander("展開偵錯日誌"):
            st.write("目前 API 可視模型：", available_models if 'available_models' in locals() else "無法獲取清單")
else:
    st.warning("警告：需配發 API 授權金鑰方可啟動核心模組。")