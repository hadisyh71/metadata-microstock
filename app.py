import streamlit as st
from groq import Groq
import base64
import pandas as pd
import io

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
# 2. CSS TEMA PUTIH (BERSIH & PRO)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1F2937; }
    [data-testid="stSidebar"] { background-color: #F9FAFB; border-right: 1px solid #E5E7EB; }
    h1, h2, h3 { color: #111827 !important; font-family: 'Segoe UI', sans-serif; }
    .stButton>button {
        background-color: #2563EB; color: white; border-radius: 8px; border: none;
        padding: 12px 24px; font-weight: 600; width: 100%; transition: 0.2s;
    }
    .stButton>button:hover { background-color: #1D4ED8; color: white; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea textarea {
        background-color: #FFFFFF; color: #111827; border: 1px solid #D1D5DB; border-radius: 6px;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI BACKEND & PARSING
# ==========================================
def get_groq_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
        return Groq(api_key=api_key)
    except Exception:
        st.error("⚠️ API Key belum dipasang di secrets.toml")
        st.stop()

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def parse_ai_response(text):
    """Memisahkan Title, Description, Keywords dari teks AI"""
    title = ""
    description = ""
    keywords = ""
    
    try:
        # Logika Parsing Sederhana
        if "TITLE:" in text and "DESCRIPTION:" in text:
            parts = text.split("TITLE:")[1].split("DESCRIPTION:")
            title = parts[0].strip()
            
            if "KEYWORDS:" in parts[1]:
                desc_parts = parts[1].split("KEYWORDS:")
                description = desc_parts[0].strip()
                keywords = desc_parts[1].strip()
            else:
                description = parts[1].strip()
    except Exception:
        # Jika format agak beda, kembalikan kosong atau raw text
        pass
        
    return title, description, keywords

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.header("⚙️ Pengaturan")
    platform = st.selectbox("Target Market:", ("Adobe Stock", "Shutterstock", "Freepik", "Getty Images"))
    lang = st.selectbox("Bahasa Output:", ("English", "Indonesian"))
    st.divider()
    st.caption("Engine: **Llama 4 Scout**")
    st.info("ℹ️ **Fitur CSV:** Setelah generate selesai, tombol download CSV akan muncul di bawah.")

# ==========================================
# 5. HALAMAN UTAMA
# ==========================================
st.title("📸 Microstock Metadata AI + CSV Export")
st.write("Generate Metadata & **Download CSV** otomatis untuk kemudahan upload.")

uploaded_files = st.file_uploader(
    "📂 Upload Foto (Max 10 File)", 
    accept_multiple_files=True, 
    type=['png', 'jpg', 'jpeg']
)

# Inisialisasi State untuk menyimpan hasil
if 'results_data' not in st.session_state:
    st.session_state.results_data = []

# Tombol Eksekusi
if st.button("🚀 PROSES FOTO SEKARANG"):
    if not uploaded_files:
        st.warning("⚠️ Tolong upload foto dulu.")
        st.stop()

    client = get_groq_client()
    st.session_state.results_data = [] # Reset hasil lama
    
    progress_bar = st.progress(0, text="Memulai analisis...")
    
    for i, file in enumerate(uploaded_files):
        current_progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(current_progress, text=f"Sedang memproses: {file.name}")
        
        try:
            base64_image = encode_image(file)
            prompt = f"""
            Analyze this image for {platform}. Output Language: {lang}.
            Output strictly in this format:
            TITLE: [Commercial SEO title, max 70 chars]
            DESCRIPTION: [Detailed description min 15 words]
            KEYWORDS: [50 keywords, comma separated]
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
            
            # Parsing Hasil untuk CSV
            p_title, p_desc, p_keys = parse_ai_response(result_text)
            
            # Simpan ke Session State
            st.session_state.results_data.append({
                "Filename": file.name,
                "Title": p_title,
                "Description": p_desc,
                "Keywords": p_keys
            })
            
            # Tampilkan Preview
            with st.expander(f"✅ Selesai: {file.name}", expanded=False):
                col_img, col_res = st.columns([1, 2])
                with col_img: st.image(file, use_container_width=True)
                with col_res: st.text_area("Metadata:", value=result_text, height=200)
                
        except Exception as e:
            st.error(f"Gagal memproses {file.name}: {e}")

    progress_bar.progress(1.0, text="✅ Analisis Selesai!")

# ==========================================
# 6. AREA DOWNLOAD CSV
# ==========================================
if st.session_state.results_data:
    st.divider()
    st.subheader("📥 Download Area")
    st.success(f"Berhasil memproses {len(st.session_state.results_data)} foto!")
    
    # Konversi ke CSV menggunakan Pandas
    df = pd.DataFrame(st.session_state.results_data)
    csv = df.to_csv(index=False).encode('utf-8')
    
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        st.download_button(
            label="📥 DOWNLOAD FILE CSV",
            data=csv,
            file_name="microstock_metadata.csv",
            mime="text/csv",
            type="primary" # Tombol menonjol
        )
    with col_d2:
        st.caption("ℹ️ **Cara Pakai CSV:** Upload file CSV ini bersamaan dengan file foto di halaman upload agency (Shutterstock/Adobe/ESP). Pastikan nama file foto tidak berubah.")
    
    # Tampilkan Tabel Preview
    with st.expander("🔍 Lihat Tabel Data CSV"):
        st.dataframe(df)
