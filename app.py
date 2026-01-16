import streamlit as st
import base64
from groq import Groq

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Microstock Metadata Generator", page_icon="📸", layout="centered")

# --- CSS SEDERHANA ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1 { color: #3B82F6; }
    .stButton>button { background-color: #3B82F6; color: white; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- SETUP GROQ API ---
# Tips: Simpan API Key di secrets.toml agar tidak perlu input manual terus
api_key = st.secrets.get("GROQ_API_KEY") 

# Jika belum ada di secrets, minta input manual
if not api_key:
    with st.sidebar:
        api_key = st.text_input("Masukkan Groq API Key:", type="password")

# --- FUNGSI HELPER GAMBAR ---
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# --- MAIN APP ---
st.title("📸 Microstock Metadata AI")
st.write("Engine: **Groq Llama Vision** (Khusus Adobe Stock & Shutterstock)")

uploaded_files = st.file_uploader("Upload Foto (Bisa Banyak)", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

if st.button("🚀 Generate Metadata") and uploaded_files:
    if not api_key:
        st.error("⚠️ API Key belum dimasukkan!")
        st.stop()

    client = Groq(api_key=api_key)
    
    # Progress Bar
    progress_bar = st.progress(0)
    
    for i, file in enumerate(uploaded_files):
        with st.expander(f"📷 Hasil untuk: {file.name}", expanded=True):
            col1, col2 = st.columns([1, 2])
            
            # Tampilkan Gambar
            with col1:
                st.image(file, use_container_width=True)
                
            # Proses AI
            with col2:
                with st.spinner("Menganalisis visual..."):
                    try:
                        # Encode gambar ke Base64 agar bisa dibaca Groq
                        base64_image = encode_image(file)
                        
                        prompt = """
                        Analyze this image for Adobe Stock / Microstock.
                        Output strictly in this format:
                        
                        TITLE: (SEO friendly title, max 70 chars)
                        DESCRIPTION: (Detailed description min 15 words)
                        KEYWORDS: (50 keywords separated by commas, sorted by relevance)
                        """

                        chat_completion = client.chat.completions.create(
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{base64_image}",
                                            },
                                        },
                                    ],
                                }
                            ],
                            model="llama-3.2-11b-vision-preview", # Model Vision Groq
                        )
                        
                        result = chat_completion.choices[0].message.content
                        st.text_area("Copy Metadata:", value=result, height=300)
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # Update progress
        progress_bar.progress((i + 1) / len(uploaded_files))

    st.success("✅ Selesai! Siap copy-paste.")
