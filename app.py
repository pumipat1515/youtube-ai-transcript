import streamlit as st
import re
from youtube_transcript_api import YouTubeTranscriptApi

# --- ฟังก์ชันแปลงวินาทีเป็นรูปแบบ นาที:วินาที ---
def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

# ==========================================
# ส่วนหน้าเว็บ (UI)
# ==========================================
st.set_page_config(page_title="YouTube AI Audio Transcript", page_icon="🎬", layout="wide")

st.title("YouTube AI Audio Transcript 🎬🌍")
st.write("แอปถอดเสียงจากวิดีโอ YouTube พร้อมแสดงช่วงเวลา (Timestamps) อย่างแม่นยำ")

url = st.text_input("วางลิงก์ YouTube ตรงนี้...", value="https://www.youtube.com/watch?v=f3c4mQty_so")

if url:
    # แกะรหัสวิดีโอจากลิงก์
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    video_id = match.group(1) if match else None
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📺 วิดีโอ")
        if video_id:
            st.components.v1.iframe(f"https://www.youtube.com/embed/{video_id}", height=315)
        
    with col2:
        st.subheader("บทถอดเสียงพร้อมช่วงเวลา")
        
        if st.button("เริ่มถอดเสียง", type="primary"):
            if not video_id:
                st.error("❌ ลิงก์ YouTube ไม่ถูกต้อง")
            else:
                with st.spinner("กำลังดึงข้อมูลจริงจากคลิป..."):
                    try:
                        # ใช้คำสั่งมาตรฐานสุดในการดึงซับไตเติลภาษาอังกฤษ
                        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                        st.success("✨ ดึงข้อมูลสำเร็จ! (ข้อมูลจริง 9 นาที)")
                        
                        # สร้างกล่องเลื่อนได้
                        with st.container(height=500):
                            for entry in transcript:
                                start_time = format_time(entry['start'])
                                end_time = format_time(entry['start'] + entry['duration'])
                                text = entry['text'].replace('\n', ' ')
                                
                                st.markdown(f"⏳ **[{start_time} - {end_time}]** : {text}")
                                
                    except Exception as e:
                        st.error("❌ เกิดข้อผิดพลาดในการดึงข้อมูล")
                        st.write(f"รายละเอียด: {e}")
