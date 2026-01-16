import streamlit as st
from groq import Groq
import base64
import pandas as pd

# ==========================================
# 1. KONFIGURASI HALAMAN (FORCE EXPAND)
# ==========================================
st.set_page_config(
    page_title="Microstock Metadata AI",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CSS "REVISI EKSTRIM" (AGAR TOMBOL JELAS)
# ==========================================
st.markdown("""
    <style>
    /* 1. BACKGROUND PUTIH BERSIH */
    .stApp {
        background-color: #FFFFFF;
        color: #111827;
    }
    
    /* 2. MEMAKSA TOMBOL SIDEBAR JADI BIRU BESAR */
    /* Ini akan mengubah panah kecil '>' menjadi tombol kotak biru yang jelas */
    button[kind="header"] {
        background-color: #2563EB !important; /* Warna Biru Terang */
        color: white !important; /* Panah Putih */
        border-radius: 8px !important;
        border: 2px solid #1D4ED8 !important;
        width: 3rem !important; /* Ukuran Besar */
        height: 3rem !important;
        opacity: 1 !important;
        z-index: 999999 !important;
        margin-top: 10px;
        margin-left: 10px;
    }
    
    /* Hover effect untuk tombol sidebar */
    button[kind="header"]:hover {
        background-color: #1D4ED8 !important;
        transform: scale(1.1);
    }

    /* 3. SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #F3F4F6;
        border-right: 2px solid #E5E7EB;
    }
    
    /* 4. HEADER & TEXT */
    h1, h2, h3 { color: #111827 !important; font-family: 'Segoe UI', sans-serif; }
    
    /* 5. TOMBOL UTAMA (PROSES) */
    .stButton>button {
        background-color: #2563EB;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        border: none;
        width: 100%;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #1E40AF;
        color: white;
    }

    /* 6. INPUT FIELDS (Jelas batasnya) */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea textarea {
        background-color: white;
        color: #111827;
        border: 1px solid #9CA3AF;
        border-radius: 6px;
    }

    /* HILANGKAN ELEMENT MENGGANGGU */
    #MainMenu, footer, header {visibility: hidden;}
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
        
        if not title and "TITLE:" in text: # Fallback parsing
            parts = text.split("TITLE:")[1].split("DESCRIPTION:")
            title = parts[0].strip()
            if "KEYWORDS:" in parts[1]:
                d_parts = parts[1].split("KEYWORDS:")
                desc = d_parts[0].strip()
                keys = d_parts[1].strip()
    except: pass
    return title, desc, keys

# ==========================================
# 4. SIDEBAR (MENU PENGATURAN)
# ==========================================
with st.sidebar:
    st.header("⚙️ SETTINGS")
    st.write("Atur target pasar di sini:")
    
    platform = st.selectbox("Target Agency:", ("Adobe Stock", "Shutterstock", "Freepik", "Getty Images"))
    # Hardcode English Output
    st.markdown("**Output Language:** English (Locked)")
    
    st.divider()
    st.info("ℹ️ **INFO:** Tombol download CSV akan muncul otomatis setelah proses selesai.")

# ==========================================
# 5. HALAMAN UTAMA
# ==========================================
st.title("📸 Microstock Metadata AI")
st.write("Generate optimized **Titles, Descriptions, & Keywords** ready for CSV Export.")

if 'results_data' not in st.session_state:
    st.session_state.results_data = []

# UPLOAD SECTION
uploaded_files = st.file_uploader(
    "📂 Upload Photos (JPG/PNG, Max 10 Files)", 
    accept_multiple_files=True, 
    type=['png', 'jpg', 'jpeg']
)

# PROCESS BUTTON
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
            
            with st.expander(f"✅ Result: {file.name}", expanded=False):
                col_img, col_res = st.columns([1, 2])
                with col_img: st.image(file, use_container_width=True)
                with col_res: st.text_area("Metadata:", value=result_text, height=200)
                
        except Exception as e:
            st.error(f"Error: {e}")

    progress_bar.progress(1.0, text="✅ Done!")
    st.success("Analysis Complete! Download CSV below.")

# ==========================================
# 6. DOWNLOAD SECTION
# ==========================================
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
