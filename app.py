import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# [系統參數設定]
st.set_page_config(page_title="戰術語音轉譯中樞", page_icon="🎙️", layout="centered")
st.title("語音文本提取系統")
st.markdown("### 系統狀態：待命\n上傳錄音檔，系統將執行降熵打擊，提取純文字資本。")

# [安全驗證與金鑰載入]
# 優先讀取雲端環境變數，若無則要求手動輸入
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.text_input("輸入 Gemini API Key 以解鎖系統", type="password")

if api_key:
    genai.configure(api_key=api_key)
    
    # [上傳介面] 支援 Line 預設的 m4a 以及其他常見格式
    uploaded_file = st.file_uploader("部署音訊檔 (.m4a, .mp3, .wav)", type=['m4a', 'mp3', 'wav'])
    
    if uploaded_file is not None:
        if st.button("啟動轉譯協議 (Execute)"):
            with st.spinner("系統解析中，正在提取時間資本..."):
                try:
                    # 步驟一：建立本地暫存檔 (維持系統穩態，不殘留垃圾)
                    file_extension = uploaded_file.name.split('.')[-1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # 步驟二：拋轉至 Gemini 雲端進行多模態解析
                    audio_file = genai.upload_file(path=tmp_path)
                    
                    # 確保檔案處於可處理狀態
                    while audio_file.state.name == "PROCESSING":
                        time.sleep(1)
                        audio_file = genai.get_file(audio_file.name)
                        
                    # 步驟三：執行精確提取
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = "你是一個精確的逐字稿轉譯員。請將此音訊完整轉換為繁體中文逐字稿。絕對不要添加任何額外的解釋、問候或總結，只需輸出原本的說話內容。"
                    response = model.generate_content([prompt, audio_file])
                    transcript = response.text
                    
                    # 步驟四：防爆鎖定與清理 (銷毀雲端與本地端暫存資產)
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
else:
    st.warning("警告：需配發 API 授權金鑰方可啟動核心模組。")