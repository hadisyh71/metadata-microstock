import streamlit as st
from groq import Groq
import base64
import pandas as pd

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Microstock Metadata AI",
    page_icon="📸",
    layout="wide"
)

# ==========================================
# 2. CSS TEMA PUTIH BERSIH
# ==========================================
st.markdown("""
    <style>
    /* Background Putih */
    .stApp {
        background-color: #FFFFFF;
        color: #111827;
    }
    
    /* Hapus Margin Atas biar Full */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Styling Header */
    h1, h2, h3 { color: #111827 !important; font-family: 'Segoe UI', sans-serif; }
    
    /* Tombol Utama */
    .stButton>button {
        background-color: #2563EB;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.8rem;
        width: 100%;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #1E40AF;
        color: white;
    }

    /* Kotak Input */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea textarea {
        background-color: #F9FAFB;
        color: #111827;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
    }

    /* Hapus Elemen Bawaan */
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;} /* Paksa Sidebar Hilang */
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI BACKEND
# ==========================================
def get_groq_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
        return Groq(api_key=api_key)
    except Exception:
        st.error("⚠️ API Key missing in secrets.toml")
        st.stop()

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def parse_ai_response(text):
    title, desc, keys = "", "", ""
    try:
        lines = text.split('\n')
        for line in lines:
            if "TITLE:" in line: title = line.replace("TITLE:", "").strip()
            elif "DESCRIPTION:" in line: desc = line.replace("DESCRIPTION:", "").strip()
            elif "KEYWORDS:" in line: keys = line.replace("KEYWORDS:", "").strip()
        
        # Fallback Logic
        if not title and "TITLE:" in text:
            parts = text.split("TITLE:")[1].split("DESCRIPTION:")
            title = parts[0].strip()
            if "KEYWORDS:" in parts[1]:
                d_parts = parts[1].split("KEYWORDS:")
                desc = d_parts[0].strip()
                keys = d_parts[1].strip()
    except: pass
    return title, desc, keys

# ==========================================
# 4. HALAMAN UTAMA (SETTINGS DI ATAS)
# ==========================================
st.title("📸 Microstock Metadata AI")
st.write("Generate optimized **Titles, Descriptions, & Keywords** ready for CSV Export.")

# --- AREA SETTINGS (Pindah ke Sini) ---
with st.container():
    st.markdown("### ⚙️ Settings")
    col_set1, col_set2, col_set3 = st.columns(3)
    
    with col_set1:
        platform = st.selectbox("Target Agency:", ("Adobe Stock", "Shutterstock", "Freepik", "Getty Images"))
    with col_set2:
        # Output language hardcoded as requested, but visible
        st.info("Output Language: **English** (Locked)")
    with col_set3:
        st.success("Engine: **Llama 4 Scout** (Active)")

st.divider()

# --- AREA UPLOAD ---
if 'results_data' not in st.session_state:
    st.session_state.results_data = []

uploaded_files = st.file_uploader(
    "📂 Upload Photos (JPG/PNG, Max 10 Files)", 
    accept_multiple_files=True, 
    type=['png', 'jpg', 'jpeg']
)

# --- TOMBOL PROSES ---
if st.button("🚀 START PROCESS"):
    if not uploaded_files:
        st.warning("⚠️ Please upload images first.")
        st.stop()

    client = get_groq_client()
    st.session_state.results_data = []
    
    progress_bar = st.progress(0, text="Starting analysis...")
    
    for i, file in enumerate(uploaded_files):
        current_progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(current_progress, text=f"Analyzing: {file.name}")
        
        try:
            base64_image = encode_image(file)
            prompt = f"""
            Analyze image for {platform}. Task: Metadata for Microstock.
            Output Format (Plain Text, English Only):
            TITLE: [Commercial SEO title, max 70 chars]
            DESCRIPTION: [Detailed description, min 15 words]
            KEYWORDS: [50 keywords, comma separated, sorted by relevance]
            """

            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        ],
                    }
                ],
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.5
            )
            
            result_text = completion.choices[0].message.content
            p_title, p_desc, p_keys = parse_ai_response(result_text)
            
            st.session_state.results_data.append({
                "Filename": file.name, "Title": p_title, "Description": p_desc, "Keywords": p_keys
            })
            
            # Tampilkan Hasil
            with st.expander(f"✅ Result: {file.name}", expanded=False):
                col_img, col_res = st.columns([1, 2])
                with col_img: st.image(file, use_container_width=True)
                with col_res: st.text_area("Metadata:", value=result_text, height=200)
                
        except Exception as e:
            st.error(f"Error: {e}")

    progress_bar.progress(1.0, text="✅ Done!")
    st.success("Analysis Complete! Download CSV below.")

# --- AREA DOWNLOAD ---
if st.session_state.results_data:
    st.divider()
    st.subheader("📥 Export Data")
    
    df = pd.DataFrame(st.session_state.results_data)
    csv = df.to_csv(index=False).encode('utf-8')
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.download_button(
            label="📥 DOWNLOAD CSV FILE",
            data=csv,
            file_name="metadata_export.csv",
            mime="text/csv",
            type="primary"
        )
    with col2:
        with st.expander("🔍 Preview Table"):
            st.dataframe(df)
