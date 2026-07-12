import streamlit as st
import whisper
import os
import re
from pytubefix import YouTube

# --- ฟังก์ชัน: ดาวน์โหลดเสียง (ระบบหมุนเวียนบอทจำลองเพื่อหลบ Error 400/403) ---
def download_audio_direct(youtube_url):
    st.info("กำลังเชื่อมต่อกับ YouTube เพื่อดึงไฟล์เสียง...")
    
    # 1. ทำความสะอาดลิงก์ (ตัดพวกเวลา &t=... ทิ้ง)
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", youtube_url)
    if not match:
        st.error("ลิงก์ YouTube ไม่ถูกต้องครับ")
        return None
    
    clean_url = f"https://www.youtube.com/watch?v={match.group(1)}"
    file_path = "temp_audio.m4a"
    
    # ลบไฟล์เก่าทิ้งก่อน (ถ้ามี)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    # 2. รายชื่อบอทจำลองที่จะสลับกันเจาะระบบ YouTube
    client_list = ['WEB', 'IOS', 'MWEB', 'ANDROID', 'ANDROID_VR']
    
    for client_name in client_list:
        try:
            st.info(f"🤖 กำลังลองดาวน์โหลดด้วยระบบจำลอง: {client_name}...")
            yt = YouTube(clean_url, client=client_name)
            audio_stream = yt.streams.filter(only_audio=True).first()
            
            if audio_stream:
                audio_stream.download(filename=file_path)
                st.success(f"ดาวน์โหลดสำเร็จด้วยระบบจำลอง: {client_name}!")
                return file_path
                
        except Exception as e:
            continue
            
    st.error("ระบบ YouTube ป้องกันหนาแน่นมากในขณะนี้ (ลองกดปุ่มใหมู่อีกครั้งเพื่อสุ่มช่องทางใหม่ครับ)")
    return None

# ==========================================
# ส่วนหน้าเว็บ (UI)
# ==========================================
st.set_page_config(page_title="YouTube AI Audio Transcript", page_icon="🎬", layout="wide")

st.title("YouTube AI Audio Transcript 🎬🌍")
st.write("แอปนี้ใช้ AI ฟังเสียงจากวิดีโอ เดาภาษาให้อัตโนมัติ แล้วแปลงเป็นข้อความ")

# ช่องใส่ลิงก์ให้อาจารย์ทดสอบ
url = st.text_input("วางลิงก์ YouTube ตรงนี้...")

# ถ้ามีการใส่ลิงก์ ให้แสดงวิดีโอและปุ่มกด
if url:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📺 วิดีโอ")
        st.video(url)
        
    with col2:
        st.subheader("บทถอดเสียงโดย AI")
        if st.button("เริ่มถอดเสียง"):
            with st.spinner("กำลังดำเนินการ..."):
                # 1. โหลดเสียงจากลิงก์
                audio_path = download_audio_direct(url)
                
                if audio_path:
                    # 2. โหลด AI
                    st.info("กำลังโหลดโมเดล AI (อาจใช้เวลาสักครู่)...")
                    model = whisper.load_model("small")
                    
                    # 3. ให้ AI ทำงาน
                    st.info("กำลังถอดเสียง...")
                    result = model.transcribe(audio_path)
                    
                    # 4. แสดงผลลัพธ์แยกตามช่วงเวลา (Timestamps)
                    st.success("ถอดเสียงสำเร็จ!")
                    
                    # ดึงข้อมูลทีละประโยคมาจัดฟอร์แมตเวลา
                    for segment in result.get("segments", []):
                        start_sec = int(segment["start"])
                        end_sec = int(segment["end"])
                        
                        # แปลงหน่วยวินาทีให้เป็นรูปแบบ นาที:วินาที (เช่น 01:23)
                        start_time = f"{start_sec // 60:02d}:{start_sec % 60:02d}"
                        end_time = f"{end_sec // 60:02d}:{end_sec % 60:02d}"
                        
                        # พิมพ์ข้อความออกมาพร้อมบอกเวลาด้านหน้า
                        st.markdown(f"⏳ **[{start_time} - {end_time}]** {segment['text']}")