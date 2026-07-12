import streamlit as st
import re
from youtube_transcript_api import YouTubeTranscriptApi

# --- ฟังก์ชัน: ดึงบทบรรยายพร้อมเวลาโดยตรงจาก YouTube ---
def get_youtube_transcript(youtube_url):
    # ดึง Video ID ออกมาจากลิงก์
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", youtube_url)
    if not match:
        st.error("ลิงก์ YouTube ไม่ถูกต้องครับ")
        return None
    
    video_id = match.group(1)
    
    try:
        # เรียกดูรายการซับไตเติลที่มีในคลิป
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # ค้นหาซับไตเติลภาษาอังกฤษหรือภาษาไทยก่อน ถ้าไม่มีจะเลือกตัวแรกสุดที่คลิปนั้นมีอัตโนมัติ
        try:
            transcript = transcript_list.find_transcript(['en', 'th'])
        except:
            transcript = transcript_list.find_transcript([])
            
        return transcript.fetch()
        
    except Exception as e:
        st.error("❌ ไม่สามารถดึงบทบรรยายได้: วิดีโอนี้อาจจะไม่มีระบบคำบรรยาย (Subtitle) หรือผู้เขียนปิดไว้ครับ")
        return None

# ==========================================
# ส่วนหน้าเว็บ (UI)
# ==========================================
st.set_page_config(page_title="YouTube AI Audio Transcript", page_icon="🎬", layout="wide")

st.title("YouTube AI Audio Transcript 🎬🌍")
st.write("แอปถอดเสียงจากวิดีโอ YouTube พร้อมแสดงช่วงเวลา (Timestamps) อย่างแม่นยำ")

# ช่องใส่ลิงก์ให้อาจารย์ทดสอบ
url = st.text_input("วางลิงก์ YouTube ตรงนี้...")

if url:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📺 วิดีโอ")
        st.video(url)
        
    with col2:
        st.subheader("บทถอดเสียงพร้อมช่วงเวลา")
        if st.button("เริ่มถอดเสียง"):
            with st.spinner("กำลังประมวลผลคำบรรยาย..."):
                data = get_youtube_transcript(url)
                
                if data:
                    st.success("ถอดเสียงสำเร็จ!")
                    
                    # วนลูปแสดงข้อความแยกตามช่วงเวลาที่กำหนด
                    for entry in data:
                        start_sec = int(entry['start'])
                        end_sec = int(entry['start'] + entry['duration'])
                        
                        # จัดฟอร์แมตให้อยู่ในรูปแบบ [นาที:วินาที] เช่น [01:23]
                        start_time = f"{start_sec // 60:02d}:{start_sec % 60:02d}"
                        end_time = f"{end_sec // 60:02d}:{end_sec % 60:02d}"
                        
                        # แสดงผลลัพธ์บนหน้าจอ
                        st.markdown(f"⏳ **[{start_time} - {end_time}]** {entry['text']}")
