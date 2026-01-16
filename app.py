import streamlit as st
from groq import Groq
import base64

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Microstock Metadata AI",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CSS TEMA PUTIH (CLEAN & PROFESSIONAL)
# ==========================================
st.markdown("""
    <style>
    /* 1. Paksa Background Putih Bersih */
    .stApp {
        background-color: #FFFFFF;
        color: #1F2937; /* Tulisan Hitam Abu Gelap (Enak di mata) */
    }
    
    /* 2. Sidebar Abu-abu Sangat Muda (Biar ada pemisah) */
    [data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E5E7EB;
    }

    /* 3. Judul & Header Jelas */
    h1, h2, h3 {
        color: #111827 !important; /* Hitam Pekat */
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* 4. Tombol Biru Profesional (Jelas & Kontras) */
    .stButton>button {
        background-color: #2563EB; /* Biru Royal */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 16px;
        width: 100%;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #1D4ED8; /* Biru lebih gelap saat hover */
        color: white;
    }
    
    /* 5. Kotak Input & Text Area (Biar kelihatan batasnya) */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea textarea {
        background-color: #FFFFFF;
        color: #111827;
        border: 1px solid #D1D5DB; /* Garis tepi abu-abu */
        border-radius: 6px;
    }
    
    /* 6. Hapus Elemen Pengganggu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI BACKEND
# ==========================================
def get_groq_client():
    try:
        # Mengambil API Key dari secrets.toml
        api_key = st.secrets["GROQ_API_KEY"]
        return Groq(api_key=api_key)
    except Exception:
        st.error("⚠️ API Key belum dipasang di secrets.toml")
        st.stop()

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# ==========================================
# 4. SIDEBAR (BERSIH & MINIMALIS)
# ==========================================
with st.sidebar:
    st.header("⚙️ Pengaturan")
    
    # Platform Selection
    platform = st.selectbox("Target Market:", ("Adobe Stock", "Shutterstock", "Freepik", "Getty Images"))
    lang = st.selectbox("Bahasa Output:", ("English", "Indonesian"))
    
    st.divider()
    st.caption("Engine: **Llama 4 Scout**")
    st.info("💡 **Tips:** Upload foto yang jelas agar AI bisa membaca detailnya dengan akurat.")

# ==========================================
# 5. HALAMAN UTAMA
# ==========================================
st.title("📸 Microstock Metadata AI")
st.write("Generate **Judul, Deskripsi, & Keyword** otomatis untuk jualan foto.")

# Area Upload
uploaded_files = st.file_uploader(
    "📂 Upload Foto Anda di sini (Max 10 File)", 
    accept_multiple_files=True, 
    type=['png', 'jpg', 'jpeg']
)

# Tombol Eksekusi
if st.button("🚀 PROSES FOTO SEKARANG"):
    
    if not uploaded_files:
        st.warning("⚠️ Tolong upload foto dulu ya.")
        st.stop()

    client = get_groq_client()
    
    # Progress Bar (Warna Biru Default Streamlit)
    progress_bar = st.progress(0, text="Memulai analisis...")
    
    for i, file in enumerate(uploaded_files):
        # Update Progress
        current_progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(current_progress, text=f"Sedang memproses: {file.name}")
        
        # Expander Hasil
        with st.expander(f"✅ Hasil Metadata: {file.name}", expanded=True):
            col_img, col_res = st.columns([1, 2])
            
            with col_img:
                st.image(file, use_container_width=True)
            
            with col_res:
                try:
                    base64_image = encode_image(file)
                    
                    # Prompt Spesifik Microstock
                    prompt = f"""
                    Analyze this image for {platform}. Output Language: {lang}.
                    Output strictly in simple text format (No Markdown Bold):
                    
                    TITLE: [Write a commercial, SEO-friendly title, max 70 chars]
                    
                    DESCRIPTION: [Write a detailed description min 15 words]
                    
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
                        model="meta-llama/llama-4-scout-17b-16e-instruct", # Model Tetap Llama 4 Scout
                        temperature=0.5
                    )
                    
                    result_text = completion.choices[0].message.content
                    st.text_area("📋 Copy Hasil di bawah:", value=result_text, height=300)
                    
                except Exception as e:
                    st.error(f"Gagal memproses gambar ini: {str(e)}")
    
    progress_bar.progress(1.0, text="✅ Selesai!")
    st.balloons()
    st.success("Semua foto berhasil diproses!")
