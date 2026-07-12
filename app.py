import streamlit as st
import os
import re
import traceback
from pytubefix import YouTube
from faster_whisper import WhisperModel

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

    error_log = []  # เก็บ error ของทุกความพยายาม เพื่อโชว์ตอนท้ายถ้าล้มเหลวทั้งหมด

    # 2. สลับ client เพื่อลองดาวน์โหลด (ตัด PoToken ออกเพราะ deprecated แล้วในเวอร์ชันปัจจุบัน)
    client_list = ['WEB', 'IOS', 'MWEB', 'ANDROID', 'ANDROID_VR']

    for client_name in client_list:
        try:
            st.info(f"🤖 กำลังลองดาวน์โหลดด้วยระบบจำลอง: {client_name}...")
            print(f"[DEBUG] Trying client: {client_name}")  # ไปโผล่ใน cloud logs ด้วย
            yt = YouTube(clean_url, client=client_name)
            audio_stream = yt.streams.filter(only_audio=True).first()

            if audio_stream:
                audio_stream.download(filename=file_path)
                st.success(f"ดาวน์โหลดสำเร็จด้วยระบบจำลอง: {client_name}!")
                return file_path
            else:
                error_log.append(f"[{client_name}] ไม่พบ audio stream")

        except Exception as e:
            err_text = f"[{client_name}] {type(e).__name__}: {e}"
            print(f"[DEBUG] {err_text}")  # ไปโผล่ใน cloud logs ด้วย
            error_log.append(err_text)
            continue

    st.error("ระบบ YouTube ป้องกันหนาแน่นมากในขณะนี้ ทุก client ล้มเหลว")
    with st.expander("🔍 ดูรายละเอียด error ของแต่ละ client (กดเพื่อขยาย)"):
        for line in error_log:
            st.code(line)
    return None

# --- โหลดโมเดล Whisper แค่ครั้งเดียว เก็บไว้ใช้ซ้ำ (ประหยัด RAM/เวลา) ---
@st.cache_resource(show_spinner=False)
def load_model():
    # ใช้ "base" + int8 เพื่อให้พอดีกับขีดจำกัด RAM 1GB ของ Streamlit Community Cloud free tier
    # ถ้ายังเจอปัญหาเรื่อง resource limit ให้ลดเป็น "tiny" (กิน RAM น้อยลงอีก แลกความแม่นยำ)
    return WhisperModel("base", device="cpu", compute_type="int8")

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
                    try:
                        # 2. โหลด AI (ใช้ cache ทำให้โหลดแค่ครั้งแรกเท่านั้น)
                        st.info("กำลังโหลดโมเดล AI (อาจใช้เวลาสักครู่ในครั้งแรก)...")
                        print("[DEBUG] Loading whisper model...")
                        model = load_model()
                        print("[DEBUG] Model loaded successfully")

                        # 3. ให้ AI ทำงาน
                        st.info("กำลังถอดเสียง...")
                        print("[DEBUG] Starting transcription...")
                        segments, info = model.transcribe(audio_path, beam_size=5)

                        # 4. แสดงผลลัพธ์แยกตามช่วงเวลา (Timestamps)
                        st.success(f"ถอดเสียงสำเร็จ! (ตรวจพบภาษา: {info.language})")

                        for segment in segments:
                            start_sec = int(segment.start)
                            end_sec = int(segment.end)

                            # แปลงหน่วยวินาทีให้เป็นรูปแบบ นาที:วินาที (เช่น 01:23)
                            start_time = f"{start_sec // 60:02d}:{start_sec % 60:02d}"
                            end_time = f"{end_sec // 60:02d}:{end_sec % 60:02d}"

                            # พิมพ์ข้อความออกมาพร้อมบอกเวลาด้านหน้า
                            st.markdown(f"⏳ **[{start_time} - {end_time}]** {segment.text.strip()}")

                        # ลบไฟล์เสียงชั่วคราวทิ้งหลังใช้งานเสร็จ เพื่อประหยัดพื้นที่ดิสก์
                        if os.path.exists(audio_path):
                            os.remove(audio_path)

                    except Exception as e:
                        print(f"[DEBUG] Transcription error: {traceback.format_exc()}")
                        st.error("⚠️ เกิดข้อผิดพลาดระหว่างการถอดเสียงด้วย AI")
                        st.exception(e)
