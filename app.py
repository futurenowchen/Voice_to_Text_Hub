import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

st.set_page_config(page_title="戰術語音轉譯中樞", page_icon="🎙️")
st.title("語音文本提取系統 v1.1")

api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.text_input("輸入 Gemini API Key", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # [戰場偵查] 獲取可用模型清單
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # [自動校準邏輯]
        # 優先搜尋路徑中包含 flash 的模型
        target_model = ""
        for m in ["models/gemini-1.5-flash-latest", "models/gemini-1.5-flash", "gemini-1.5-flash"]:
            if m in available_models or f"models/{m}" in available_models:
                target_model = m
                break
        
        if not target_model and available_models:
            target_model = available_models[0] # 保底方案：使用清單中第一個可用模型

        st.info(f"系統已鎖定戰術引擎：`{target_model}`")
        
        uploaded_file = st.file_uploader("部署音訊檔 (.m4a, .mp3, .wav)", type=['m4a', 'mp3', 'wav'])
        
        if uploaded_file and st.button("啟動轉譯協議 (Execute)"):
            with st.spinner("執行降熵打擊中..."):
                file_extension = uploaded_file.name.split('.')[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                audio_file = genai.upload_file(path=tmp_path)
                
                while audio_file.state.name == "PROCESSING":
                    time.sleep(1)
                    audio_file = genai.get_file(audio_file.name)
                
                # 使用偵查到的正確名稱進行呼叫
                model = genai.GenerativeModel(model_name=target_model)
                prompt = "你是一個精確的逐字稿轉譯員。請將此音訊完整轉換為繁體中文逐字稿。絕對不要添加任何額外的解釋、問候或總結，只需輸出原本的說話內容。"
                
                response = model.generate_content([prompt, audio_file])
                
                st.success("轉譯完成。")
                st.text_area("純文字文本", response.text, height=300)
                
                # 清理
                genai.delete_file(audio_file.name)
                os.unlink(tmp_path)

    except Exception as e:
        st.error(f"偵測到系統異常：{str(e)}")
        with st.expander("查看診斷數據"):
            st.write("目前 API 可視模型：", available_models if 'available_models' in locals() else "無法獲取清單")