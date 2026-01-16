import streamlit as st
from groq import Groq
import base64

# ==========================================
# 1. KONFIGURASI HALAMAN (Wajib Paling Atas)
# ==========================================
st.set_page_config(
    page_title="Universal AI - Microstock Engine",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CSS & STYLING (TEMA ASLI ANDA - 100% SAMA)
# ==========================================
st.markdown("""
    <style>
    /* HIDE DEFAULT STREAMLIT ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* MAIN THEME COLORS */
    .stApp {
        background-color: #0B0F19;
        color: #F3F4F6;
    }
    
    /* BUTTON STYLING (GRADIENT) */
    .stButton>button {
        background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 100%);
        color: white;
        border-radius: 12px;
        border: none;
        font-weight: 600;
        width: 100%;
        padding: 10px 0;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* INPUT & SELECTBOX STYLING */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    /* EXPANDER STYLING */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        color: white !important;
    }
    
    /* TEXT AREA STYLING */
    .stTextArea textarea {
        background-color: #111827 !important;
        color: #E5E7EB !important;
        border: 1px solid #374151;
    }
    
    /* SUCCESS/ERROR BOX STYLING */
    .stSuccess, .stError, .stInfo, .stWarning {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border-radius: 10px;
    }
    
    /* HEADER TEXT */
    h1, h2, h3 {
        color: #F3F4F6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI BACKEND (API KEY DARI SECRETS)
# ==========================================
def get_groq_client():
    # Mengambil API Key langsung dari Secrets (Server)
    # Tidak perlu input manual di web
    try:
        api_key = st.secrets["GROQ_API_KEY"]
        return Groq(api_key=api_key)
    except Exception:
        st.error("⚠️ API Key tidak ditemukan di secrets.toml!")
        st.stop()

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# ==========================================
# 4. SIDEBAR (TAMPILAN KONTROL)
# ==========================================
with st.sidebar:
    st.title("🌐 PUSAT KONTROL")
    st.caption("Mode: **Microstock Metadata Specialist**")
    
    st.divider()
    
    # Status Koneksi
    st.success("✅ System Online")
    st.markdown(f"🤖 **Model:** `Llama 4 Scout`")
    st.markdown("🔑 **Auth:** `Secure API (Secrets)`")
    
    st.divider()
    
    st.info("""
    **Fitur Aktif:**
    - Auto Title Generator
    - Description Writer
    - 50 Keywords Extractor
    - Platform: Adobe Stock / Shutterstock
    """)

# ==========================================
# 5. HALAMAN UTAMA (MAIN UI)
# ==========================================
st.title("✨ Universal AI Control Center")
st.subheader("📸 Microstock Metadata Generator")

# Pilihan Platform & Bahasa
col1, col2 = st.columns([2, 1])
with col1:
    platform = st.selectbox("Target Platform:", ("Adobe Stock", "Shutterstock", "Freepik", "Getty Images"))
with col2:
    lang = st.selectbox("Output Language:", ("English", "Indonesian", "Spanish"))

# Area Upload
uploaded_files = st.file_uploader(
    "📂 Upload Aset Foto (Max 10 File)", 
    accept_multiple_files=True, 
    type=['png', 'jpg', 'jpeg']
)

# Tombol Eksekusi
if st.button("🚀 JALANKAN ENGINE", key="run_btn"):
    
    if not uploaded_files:
        st.warning("⚠️ Mohon upload foto terlebih dahulu.")
        st.stop()

    # Inisialisasi Client Groq dari Secrets
    client = get_groq_client()
    
    # Progress Bar
    progress_bar = st.progress(0, text="Sedang memproses antrean...")
    
    for i, file in enumerate(uploaded_files):
        current_progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(current_progress, text=f"Menganalisis: {file.name}")
        
        with st.expander(f"✅ Hasil Metadata: {file.name}", expanded=True):
            col_img, col_res = st.columns([1, 2])
            
            with col_img:
                st.image(file, use_container_width=True)
            
            with col_res:
                try:
                    # Encoding Gambar
                    base64_image = encode_image(file)
                    
                    # Prompt Khusus Microstock
                    prompt = f"""
                    Analyze this image for {platform}. Language: {lang}.
                    Output strictly in this format (Plain Text):
                    
                    TITLE: [Commercial SEO title, max 70 chars]
                    
                    DESCRIPTION: [Detailed description min 15 words]
                    
                    KEYWORDS: [50 keywords, comma separated, sorted by relevance]
                    """

                    # Request ke Llama 4 Scout (Fixed Model)
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                                ],
                            }
                        ],
                        model="meta-llama/llama-4-scout-17b-16e-instruct", # MODEL DIKUNCI
                        temperature=0.5
                    )
                    
                    result_text = chat_completion.choices[0].message.content
                    st.text_area("📋 Copy Hasil:", value=result_text, height=350)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    progress_bar.progress(1.0, text="✅ Selesai!")
    st.success("Semua file berhasil dianalisis!")
