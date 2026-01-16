import streamlit as st
import base64
from groq import Groq

# --- KONFIGURASI MODEL (Llama 4 Scout) ---
MODEL_ID = "meta-llama/llama-4-scout-17b-16e-instruct"

st.set_page_config(page_title="Microstock Metadata Generator", page_icon="📸", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1 { color: #3B82F6; }
    .stButton>button { background-color: #3B82F6; color: white; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- API KEY ---
api_key = st.secrets.get("GROQ_API_KEY") 
if not api_key:
    with st.sidebar:
        api_key = st.text_input("Masukkan Groq API Key:", type="password")

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

st.title("📸 Microstock Metadata AI")
st.caption(f"Powered by: **{MODEL_ID}**")

uploaded_files = st.file_uploader("Upload Foto", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])

if st.button("🚀 Generate Metadata") and uploaded_files:
    if not api_key: st.error("API Key kosong!"); st.stop()

    client = Groq(api_key=api_key)
    progress_bar = st.progress(0)
    
    for i, file in enumerate(uploaded_files):
        with st.expander(f"📷 Hasil: {file.name}", expanded=True):
            col1, col2 = st.columns([1, 2])
            with col1: st.image(file, use_container_width=True)
            with col2:
                with st.spinner("Llama 4 Scout sedang bekerja..."):
                    try:
                        base64_image = encode_image(file)
                        prompt = "Analyze this image for Adobe Stock. Output strictly: TITLE, DESCRIPTION, 50 KEYWORDS."

                        # Request ke Llama 4 Scout
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
                            model=MODEL_ID, # KEMBALI KE LLAMA 4 SCOUT
                        )
                        st.text_area("Metadata:", value=chat_completion.choices[0].message.content, height=300)
                    except Exception as e:
                        st.error(f"Error: {e}")
        progress_bar.progress((i + 1) / len(uploaded_files))
    st.success("Selesai!")
