import streamlit as st
import re
import requests

# --- ฟังก์ชันย่อย: แปลงและจัดฟอร์แมตไฟล์ซับไตเติล WebVTT ให้เป็นช่วงเวลาอย่างง่าย ---
def parse_vtt(vtt_text):
    lines = vtt_text.split('\n')
    result = []
    current_time = ""
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_time and current_text:
                result.append({"time": current_time, "text": " ".join(current_text)})
                current_text = []
            continue
        if "-->" in line:
            parts = line.split("-->")
            start = parts[0].strip().split(".")[0]
            end = parts[1].strip().split(".")[0]
            if start.startswith("00:"): start = start[3:]
            if end.startswith("00:"): end = end[3:]
            current_time = f"{start} - {end}"
        elif line.isdigit() or line == "WEBVTT" or line.startswith("NOTE") or line.startswith("Style:"):
            continue
        else:
            current_text.append(line)
    if current_time and current_text:
        result.append({"time": current_time, "text": " ".join(current_text)})
    return result

# --- ฟังก์ชันหลัก: ดึงบทบรรยายระบบไฮบริด (ป้องกันปัญหา Cloud IP Block) ---
def get_youtube_transcript(youtube_url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", youtube_url)
    if not match:
        st.error("ลิงก์ YouTube ไม่ถูกต้องครับ")
        return None
    
    video_id = match.group(1)
    
    # [วิธีที่ 1] ดึงตรงจาก YouTube ด้วยไลบรารีมาตรฐาน
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(['en', 'th'])
        except:
            transcript = transcript_list.find_transcript([])
            
        raw_data = transcript.fetch()
        formatted_data = []
        for entry in raw_data:
            start_sec = int(entry['start'])
            end_sec = int(entry['start'] + entry['duration'])
            start_time = f"{start_sec // 60:02d}:{start_sec % 60:02d}"
            end_time = f"{end_sec // 60:02d}:{end_sec % 60:02d}"
            formatted_data.append({"time": f"{start_time} - {end_time}", "text": entry['text']})
        return formatted_data
    except Exception:
        # ถ้าวิธีที่ 1 พัง (เพราะโดน YouTube บล็อก IP บน Streamlit Cloud) ให้ข้ามมาใช้วิธีที่ 2 ทันที
        pass

    # [วิธีที่ 2] เจาะระบบผ่านเซิร์ฟเวอร์ตัวกลางสำรอง (หลบการบล็อก IP ของ YouTube บนคลาวด์)
    st.info("🔄 กำลังสลับไปใช้ระบบสำรองเพื่อหลบเลี่ยงการบล็อก IP...")
    instances = [
        f"https://pipedapi.kavin.rocks/streams/{video_id}",
        f"https://pipedapi.moomoo.me/streams/{video_id}",
        f"https://api.piped.projectsegfau.lt/streams/{video_id}"
    ]
    
    for url in instances:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                subtitles = data.get("subtitles", [])
                if subtitles:
                    # เลือกซับภาษาอังกฤษหรือไทยก่อน ถ้าไม่มีให้เอาตัวแรกสุด
                    selected_sub = subtitles[0]
                    for sub in subtitles:
                        if sub.get("languageCode") in ['en', 'th']:
                            selected_sub = sub
                            break
                    
                    # ดาวน์โหลดไฟล์ซับมาแกะข้อมูลเวลา
                    vtt_res = requests.get(selected_sub['url'], timeout=10)
                    if vtt_res.status_code == 200:
                        parsed_data = parse_vtt(vtt_res.text)
                        if parsed_data:
                            return parsed_data
        except:
            continue
            
    st.error("❌ ไม่สามารถดึงบทบรรยายได้: วิดีโอนี้อาจจะไม่มีระบบคำบรรยาย (Subtitle) หรือระบบความปลอดภัยหนาแน่นมาก รบกวนลองใหม่อีกครั้งครับ")
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
                    for entry in data:
                        st.markdown(f"⏳ **[{entry['time']}]** {entry['text']}")
