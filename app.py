import streamlit as st
from groq import Groq
import base64
import time

# ==========================================
# 1. KONFIGURASI HALAMAN & STATE
# ==========================================
st.set_page_config(
    page_title="Microstock AI Metadata Pro",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CSS & STYLING (TEMA MEWAH ANDA - DIPERTAHANKAN)
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
    
    /* INPUT FIELDS STYLING */
    .stTextInput>div>div>input {
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
    
    /* SUCCESS/ERROR BOX */
    .stSuccess, .stError, .stInfo {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px;
        color: white !important;
    }

    /* HEADER BANNER */
    .header-banner {
        background: linear-gradient(90deg, #F59E0B 0%, #D97706 100%);
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
        color: black;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI LOGIKA (BACKEND)
# ==========================================
def encode_image(image_file):
    """Mengubah gambar jadi Base64 biar bisa dilihat Llama 4"""
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# ==========================================
# 4. SIDEBAR (KONTROL)
# ==========================================
with st.sidebar:
    st.header("🌐 PUSAT KONTROL")
    st.caption("Engine: **Llama 4 Scout (Groq)**")
    
    # Input API Key (Simpel, tanpa sistem token rumit)
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Masukkan Groq API Key:", type="password", help="Dapatkan gratis di console.groq.com")
    else:
        st.success("✅ API Key Terdeteksi (Secrets)")

    st.divider()
    
    st.info("""
    **Fitur Aplikasi:**
    - Auto Title (SEO Friendly)
    - Detailed Description
    - 50 Keywords Generator
    - Adobe Stock & Shutterstock Ready
    """)

# ==========================================
# 5. MAIN PAGE (TAMPILAN UTAMA)
# ==========================================
st.title("📸 Microstock Metadata Pro")
st.markdown("""<div style="color: #9CA3AF; margin-bottom: 20px;">
Optimalkan penjualan foto Anda dengan metadata otomatis berbasis AI Vision.
</div>""", unsafe_allow_html=True)

# Container Upload
with st.container():
    uploaded_files = st.file_uploader(
        "📂 Upload Foto (Max 10 File sekaligus)", 
        accept_multiple_files=True, 
        type=['png', 'jpg', 'jpeg']
    )

# TOMBOL EKSEKUSI
if st.button("🚀 GENERATE METADATA SEKARANG"):
    
    if not api_key:
        st.error("⚠️ Mohon masukkan API Key Groq di Sidebar sebelah kiri.")
        st.stop()
        
    if not uploaded_files:
        st.warning("⚠️ Belum ada foto yang diupload.")
        st.stop()

    client = Groq(api_key=api_key)
    
    # Progress Bar Mewah
    progress_text = "Sedang menganalisis visual..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, file in enumerate(uploaded_files):
        # Update Progress
        percent = (i) / len(uploaded_files)
        my_bar.progress(percent, text=f"Memproses foto {i+1} dari {len(uploaded_files)}: {file.name}")
        
        # UI Hasil per Foto
        with st.expander(f"✅ Hasil: {file.name}", expanded=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(file, use_container_width=True)
            
            with col2:
                try:
                    # Proses AI (Llama 4 Scout)
                    base64_image = encode_image(file)
                    
                    # Prompt Khusus Microstock
                    prompt = """
                    Analyze this image for Microstock (Adobe Stock/Shutterstock).
                    Output strictly in this format (No markdown bolding, just plain text):
                    
                    TITLE: [Write a commercial, SEO-friendly title, max 70 chars]
                    DESCRIPTION: [Write a detailed description min 15 words]
                    KEYWORDS: [Generate 50 keywords separated by commas, sorted by relevance]
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
                        model="meta-llama/llama-4-scout-17b-16e-instruct", # MODEL YANG ANDA MINTA
                        temperature=0.5
                    )
                    
                    result_text = completion.choices[0].message.content
                    st.text_area("📋 Copy Metadata:", value=result_text, height=300)
                    
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {str(e)}")
                    
    my_bar.progress(1.0, text="✅ Semua proses selesai!")
    st.success("🎉 Metadata berhasil dibuat! Silakan copy hasilnya.")
