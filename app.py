import streamlit as st
import re
import whisper
import yt_dlp
import os

# ตั้งค่าหน้าตาของเว็บ
st.set_page_config(page_title="YouTube AI Auto-Detect Transcript", layout="wide")

# โหลดโมเดล AI ของ Whisper
@st.cache_resource
def load_whisper_model():
    # ใช้รุ่น "small" เพื่อให้ AI รองรับทุกภาษา และมีความฉลาดพอที่จะเดาภาษาได้แม่นยำ
    return whisper.load_model("medium")

st.title("YouTube AI Audio Transcript 🎬🌍")
st.write("แอปนี้ใช้ AI ฟังเสียงจากวิดีโอ เดาภาษาให้อัตโนมัติ แล้วแปลงเป็นข้อความ")

# ฟังก์ชันดึง Video ID
def get_youtube_id(url):
    regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

# ฟังก์ชันแปลงเวลา
def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

# --- ส่วนรับอินพุตจากผู้ใช้ ---
url_input = st.text_input("วางลิงก์ YouTube ตรงนี้...", placeholder="https://www.youtube.com/watch?v=...")

if url_input:
    video_id = get_youtube_id(url_input)
    
    if not video_id:
        st.error("❌ กรุณาใส่ลิงก์ YouTube ให้ถูกต้องด้วยครับ")
    else:
        # แบ่งหน้าจอเป็น 2 ฝั่ง
        col1, col2 = st.columns([1.4, 1])
        
        with col1:
            st.subheader("📺 วิดีโอ")
            st.video(f"https://www.youtube.com/watch?v={video_id}")
            
        with col2:
            st.subheader("บทถอดเสียงโดย AI")
            status_area = st.empty()
            
            # โหลด AI เตรียมไว้
            status_area.info("⏳ กำลังโหลดโมเดล AI...")
            model = load_whisper_model()
            
            status_area.info("⏳ กำลังดาวน์โหลดและวิเคราะห์ภาษา (อาจใช้เวลาสักครู่ ขึ้นอยู่กับความยาวคลิป)...")
            
            audio_filename = "temp_audio.mp3"
            
            try:
                # 1. โหลดเฉพาะเสียงจาก YouTube
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': 'temp_audio.%(ext)s', 
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'quiet': True,
                    'noplaylist': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url_input])
                
                # 2. ให้ AI ฟังและถอดเสียง (ปล่อยว่างไว้ AI จะเดาภาษาเองอัตโนมัติ)
                result = model.transcribe(audio_filename)
                
                status_area.success(f"✅ AI ถอดเสียงเสร็จเรียบร้อย!")
                
                # 3. แสดงผลลงในกรอบแบบเลื่อนได้ (Scrollbox)
                with st.container(height=450):
                    for segment in result["segments"]:
                        time_tag = format_time(segment["start"])
                        text = segment["text"].strip()
                        
                        if text: # ตรวจสอบว่ามีข้อความจริงๆ ถึงจะแสดงผล
                            st.markdown(f"""
                            <div style="margin: 8px 0; padding: 10px; border-left: 4px solid #0052cc; background-color: #f0f7ff; border-radius: 0 10px 10px 0; color: #2b2b2b;">
                                <span style="color: #0052cc; font-weight: bold; background: #dceafe; padding: 2px 6px; border-radius: 4px; margin-right: 8px;">[{time_tag}]</span>
                                {text}
                            </div>
                            """, unsafe_allow_html=True)
                            
            except Exception as e:
                status_area.error("⚠️ เกิดข้อผิดพลาดในการทำงาน")
                st.warning(f"รายละเอียด: {e}")
                
            finally:
                # 4. ลบไฟล์เสียงชั่วคราวทิ้งเสมอ
                if os.path.exists(audio_filename):
                    try:
                        os.remove(audio_filename)
                    except:
                        pass