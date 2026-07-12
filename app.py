import streamlit as st
import re
import requests

# --- ฟังก์ชันย่อย: แกะและจัดฟอร์แมตไฟล์ซับไตเติล WebVTT ให้แสดงผลสวยงาม ---
def parse_vtt(vtt_text):
    lines = vtt_text.split('\n')
    result = []
    current_time = ""
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_time and current_text:
                clean_text = " ".join(current_text)
                clean_text = re.sub(r'<[^>]*>', '', clean_text) # ลบแท็กส่วนเกินถ้ามี
                if clean_text:
                    result.append({"time": current_time, "text": clean_text})
                current_text = []
            continue
        if "-->" in line:
            parts = line.split("-->")
            start = parts[0].strip().split(".")[0].split(",")[0]
            end = parts[1].strip().split(".")[0].split(",")[0]
            if start.startswith("00:"): start = start[3:]
            if end.startswith("00:"): end = end[3:]
            current_time = f"{start} - {end}"
        elif line.isdigit() or line == "WEBVTT" or line.startswith("NOTE") or line.startswith("Style:"):
            continue
        else:
            current_text.append(line)
            
    if current_time and current_text:
        clean_text = " ".join(current_text)
        clean_text = re.sub(r'<[^>]*>', '', clean_text)
        if clean_text:
            result.append({"time": current_time, "text": clean_text})
            
    return result

# --- ฟังก์ชันหลัก: ดึงบทบรรยายผ่านเครือข่ายเซิร์ฟเวอร์กระจายศูนย์ทั่วโลก (Invidious Network) ---
def get_youtube_transcript_decentralized(youtube_url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", youtube_url)
    if not match:
        st.error("ลิงก์ YouTube ไม่ถูกต้องครับ")
        return None
    
    video_id = match.group(1)
    
    # รายชื่อเซิร์ฟเวอร์อิสระคุณภาพสูง (กระจายตัวอยู่คนละประเทศ ป้องกันการโดนบล็อกพร้อมกัน)
    invidious_instances = [
        "https://yewtu.be",
        "https://iv.melmac.space",
        "https://invidious.nerdvpn.de",
        "https://invidious.flokinet.to",
        "https://invidious.perennialte.ch"
    ]
    
    for instance in invidious_instances:
        try:
            st.info(f"🔄 กำลังดึงข้อมูลผ่านระบบกระจายสายหลัก: {instance.split('//')[1]}...")
            
            # 1. ยิงไปขอข้อมูลรายละเอียดวิดีโอและซับไตเติลจากอินสแตนซ์นั้นๆ
            api_url = f"{instance}/api/v1/videos/{video_id}"
            res = requests.get(api_url, timeout=7)
            
            if res.status_code == 200:
                video_data = res.json()
                captions = video_data.get("captions", [])
                
                if not captions:
                    continue # ถ้าไม่มีไฟล์ซับในเซิร์ฟเวอร์ตัวนี้ ให้ข้ามไปลองตัวถัดไป
                
                # 2. เลือกซับไตเติล (พยายามหาภาษาอังกฤษ 'en' หรือภาษาไทย 'th' ก่อน)
                selected_caption = captions[0]
                for cap in captions:
                    if cap.get("languageCode") in ['en', 'th']:
                        selected_caption = cap
                        break
                
                # 3. ดาวน์โหลดเนื้อหาซับไตเติลในฟอร์แมต WebVTT
                caption_url = f"{instance}{selected_caption['url']}&format=vtt"
                sub_res = requests.get(caption_url, timeout=7)
                
                if sub_res.status_code == 200 and "WEBVTT" in sub_res.text:
                    parsed_lines = parse_vtt(sub_res.text)
                    if parsed_lines:
                        st.success(f"✨ ดึงข้อมูลสำเร็จผ่านเซิร์ฟเวอร์: {instance.split('//')[1]}")
                        return parsed_lines
        except Exception:
            continue # เซิร์ฟเวอร์นี้ล่มหรือติดขัด สลับไปตัวถัดไปทันทีแบบไร้รอยต่อ
            
    st.error("❌ ระบบดึงข้อมูลจาก YouTube ถูกจำกัดการเข้าถึงเนื่องจากผู้ใช้งานหนาแน่น กรุณารอสักครู่แล้วลองกดใหมู่อีกครั้งนะครับ")
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
                data = get_youtube_transcript_decentralized(url)
                
                if data:
                    st.success("ถอดเสียงสำเร็จ!")
                    for entry in data:
                        st.markdown(f"⏳ **[{entry['time']}]** {entry['text']}")
