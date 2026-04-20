import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# [系統參數設定]
st.set_page_config(page_title="戰術語音轉譯中樞", page_icon="🎙️")
st.title("語音文本提取系統 v1.2 (iOS 解鎖版)")
st.markdown("### 系統狀態：待命\n執行降熵打擊，將非結構化語音轉換為純文字資產。")

# [安全驗證與金鑰載入]
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.text_input("輸入 Gemini API Key 以解鎖系統", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # [戰場偵查] 獲取可用模型清單，防禦 API 版本偏移
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # [自動校準邏輯] 優先鎖定 flash 高速模型
        target_model = ""
        for m in ["models/gemini-1.5-flash-latest", "models/gemini-1.5-flash", "gemini-1.5-flash"]:
            if m in available_models or f"models/{m}" in available_models:
                target_model = m
                break
        
        if not target_model and available_models:
            target_model = available_models[0]

        st.info(f"系統已鎖定戰術引擎：`{target_model}`")
        
        # [戰術解鎖] 撤除前端 type 限制，擊穿 iOS 灰色鎖定
        uploaded_file = st.file_uploader("部署音訊檔 (全格式解鎖，請直接從『我的 iPhone』選取)", type=None)
        
        if uploaded_file:
            # [後端防爆防護] 在伺服器端檢查副檔名
            file_ext = uploaded_file.name.split('.')[-1].lower()
            SUPPORTED_EXTS = ['m4a', 'mp3', 'wav', 'aac', 'ogg', 'flac']
            
            if file_ext not in SUPPORTED_EXTS:
                st.error(f"⚠️ 攔截：偵測到非預期格式 (.{file_ext})。請確保上傳的是音訊資產。")
            else:
                if st.button("啟動轉譯協議 (Execute)"):
                    with st.spinner("系統解析中，提取時間資本..."):
                        # 步驟一：建立本地暫存檔
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        # 步驟二：拋轉至 Gemini 雲端進行多模態解析
                        audio_file = genai.upload_file(path=tmp_path)
                        
                        while audio_file.state.name == "PROCESSING":
                            time.sleep(1)
                            audio_file = genai.get_file(audio_file.name)
                            
                        # 步驟三：執行精確提取
                        model = genai.GenerativeModel(model_name=target_model)
                        prompt = "你是一個精確的逐字稿轉譯員。請將此音訊完整轉換為繁體中文逐字稿。絕對不要添加任何額外的解釋、問候或總結，只需輸出原本的說話內容。"
                        
                        response = model.generate_content([prompt, audio_file])
                        transcript = response.text
                        
                        # 步驟四：防爆清理 (銷毀雲端與本地端暫存資產，維持低熵穩態)
                        genai.delete_file(audio_file.name)
                        os.unlink(tmp_path)
                        
                        # 步驟五：輸出戰術成果
                        st.success("轉譯完成。")
                        st.text_area("純文字文本", transcript, height=300)
                        
                        st.download_button(
                            label="下載文本 (.txt)",
                            data=transcript,
                            file_name=f"transcript_{int(time.time())}.txt",
                            mime="text/plain"
                        )

    except Exception as e:
        st.error(f"系統錯誤：{str(e)}")
        with st.expander("展開偵錯日誌"):
            st.write("目前 API 可視模型：", available_models if 'available_models' in locals() else "無法獲取清單")
else:
    st.warning("警告：需配發 API 授權金鑰方可啟動核心模組。")