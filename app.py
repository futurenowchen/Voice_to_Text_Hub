import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# [系統參數設定]
st.set_page_config(page_title="戰術語音轉譯中樞", page_icon="🎙️", layout="centered")
st.title("語音文本提取系統 v2.0 (批次突擊版)")
st.markdown("### 系統狀態：待命\n支援批次部署音訊，系統將自動執行序列降熵打擊，並輸出接續文本。")

# [安全驗證與金鑰載入]
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.text_input("輸入 Gemini API Key 以解鎖系統", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # [戰場偵查] 獲取可用模型清單
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # [自動校準邏輯]
        target_model = ""
        for m in ["models/gemini-1.5-flash-latest", "models/gemini-1.5-flash", "gemini-1.5-flash"]:
            if m in available_models or f"models/{m}" in available_models:
                target_model = m
                break
        if not target_model and available_models:
            target_model = available_models[0]

        st.info(f"系統已鎖定戰術引擎：`{target_model}`")
        
        # [戰術升級] 開啟 accept_multiple_files 實現批次上傳
        uploaded_files = st.file_uploader(
            "部署音訊檔 (全格式解鎖，可一次選取多個檔案)", 
            type=None, 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            SUPPORTED_EXTS = ['m4a', 'mp3', 'wav', 'aac', 'ogg', 'flac', 'mp4']
            valid_files = []
            
            # [前端防爆檢查] 過濾無效資產
            for f in uploaded_files:
                ext = f.name.split('.')[-1].lower()
                if ext in SUPPORTED_EXTS:
                    valid_files.append(f)
                else:
                    st.warning(f"⚠️ 已排除非音訊格式：{f.name}")
            
            if valid_files and st.button(f"啟動批次轉譯協議 (共 {len(valid_files)} 個檔案)"):
                
                # 初始化進度條與總文本容器
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
                        
                        # [文本縫合] 將結果附加至總文本，並標示來源錨點
                        master_transcript += f"### 【檔案：{file.name}】\n"
                        master_transcript += response.text.strip() + "\n\n---\n\n"
                        
                        # 步驟四：防爆清理
                        genai.delete_file(audio_file.name)
                        os.unlink(tmp_path)
                        
                        # 更新進度，並強制系統冷卻 2 秒，避免觸發 API 頻率紅線 (Rate Limit)
                        progress_bar.progress((index + 1) / total_files)
                        if index < total_files - 1:
                            time.sleep(2) 
                            
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
else:
    st.warning("警告：需配發 API 授權金鑰方可啟動核心模組。")