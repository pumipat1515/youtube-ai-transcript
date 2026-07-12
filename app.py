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
                clean_text = re.sub(r'<[^>]*>', '', clean_text) # ลบแท็กแปลกๆ ออก
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

# --- ฟังก์ชันหลัก: ดึงบทบรรยายผ่านระบบเครือข่ายไฮบริด 10 สถานีทั่วโลก ---
def get_youtube_transcript_ultimate(youtube_url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", youtube_url)
    if not match:
        st.error("ลิงก์ YouTube ไม่ถูกต้องครับ")
        return None
    
    video_id = match.group(1)
    
    # 🌟 กลุ่มที่ 1: Piped Engines (เด่นเรื่องการสลับรัน Proxy หนีการบล็อกของ YouTube)
    piped_instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.tokyo.privacydev.net",
        "https://pipedapi.moomoo.me",
        "https://pipedapi.synopy.org",
        "https://api.piped.projectsegfau.lt"
    ]
    
    # 🌟 กลุ่มที่ 2: Invidious Engines (เซิร์ฟเวอร์อิสระกระจายตัวทั่วโลก)
    invidious_instances = [
        "https://yewtu.be",
        "https://iv.melmac.space",
        "https://invidious.nerdvpn.de",
        "https://invidious.flokinet.to",
        "https://invidious.privacydev.net"
    ]
    
    # --- ลูปค่ายที่ 1: ลองเจาะด้วย Piped ก่อน ---
    for instance in piped_instances:
        try:
            st.info(f"⚡ กำลังลองผ่านช่องทางด่วน Piped: {instance.split('//')[1]}...")
            res = requests.get(f"{instance}/streams/{video_id}", timeout=5)
            if res.status_code == 200:
                data = res.json()
                subtitles = data.get("subtitles", [])
                if subtitles:
                    selected_sub = subtitles[0]
                    for sub in subtitles:
                        if sub.get("languageCode") in ['en', 'th']:
                            selected_sub = sub
                            break
                    
                    vtt_res = requests.get(selected_sub['url'], timeout=5)
                    if vtt_res.status_code == 200:
                        parsed_data = parse_vtt(vtt_res.text)
                        if parsed_data:
                            st.success(f"✨ ทะลวงสำเร็จผ่านช่องทาง: {instance.split('//')[1]}")
                            return parsed_data
        except:
            continue

    # --- ลูปค่ายที่ 2: ถ้าค่ายแรกติดบล็อกหมด ให้สลับมาใช้ค่าย Invidious ทันที ---
    for instance in invidious_instances:
        try:
            st.info(f"🔄 ช่องทางหลักหนาแน่น กำลังสลับไปสถานีสำรอง: {instance.split('//')[1]}...")
            api_url = f"{instance}/api/v1/videos/{video_id}"
            res = requests.get(api_url, timeout=5)
            
            if res.status_code == 200:
                video_data = res.json()
                captions = video_data.get("captions", [])
                if captions:
                    selected_caption = captions[0]
                    for cap in captions:
                        if cap.get("languageCode") in ['en', 'th']:
                            selected_caption = cap
                            break
                    
                    caption_url = f"{instance}{selected_caption['url']}&format=vtt"
                    sub_res = requests.get(caption_url, timeout=5)
                    if sub_res.status_code == 200 and "WEBVTT" in sub_res.text:
                        parsed_lines = parse_vtt(sub_res.text)
                        if parsed_lines:
                            st.success(f"✨ ทะลวงสำเร็จผ่านสถานีสำรอง: {instance.split('//')[1]}")
                            return parsed_lines
        except:
            continue
            
    st.error("❌ YouTube ปิดกั้นการเชื่อมต่อหนาแน่นมากในนาทีนี้ กรุณารอสัก 10 วินาทีแล้วลองกดปุ่มใหมู่อีกครั้งนะครับ")
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
                data = get_youtube_transcript_ultimate(url)
                
                if data:
                    st.success("ถอดเสียงสำเร็จ!")
                    for entry in data:
                        st.markdown(f"⏳ **[{entry['time']}]** {entry['text']}")
