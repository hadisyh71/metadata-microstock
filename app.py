import streamlit as st
from groq import Groq
import base64
import pandas as pd

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Microstock AI Pro",
    page_icon="✨",
    layout="wide"
)

# ==========================================
# 2. CSS PREMIUM (MODERN SAAS LOOK)
# ==========================================
st.markdown("""
    <style>
    /* IMPORT FONT (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* BACKGROUND UTAMA (Abu-abu Halus) */
    .stApp {
        background-color: #F3F4F6;
        color: #1F2937;
    }
    
    /* HAPUS PADDING ATAS BAWAAN */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* HEADER STYLE */
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: #111827;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #6B7280;
        font-size: 1.1rem;
    }

    /* CARD STYLE (KOTAK PUTIH DENGAN SHADOW) */
    .css-1r6slb0, .stExpander {
        background-color: #FFFFFF;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #E5E7EB;
        padding: 5px;
        margin-bottom: 1rem;
    }
    
    /* INPUT FIELDS (LEBIH BERSIH) */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        color: #374151 !important;
    }
    
    /* TOMBOL UTAMA (BIRU GRADASI) */
    .stButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        font-weight: 700;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 10px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(37, 99, 235, 0.3);
    }

    /* TOMBOL DOWNLOAD (HIJAU SPESIAL) */
    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 1rem !important;
        border-radius: 10px !important;
        width: 100% !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(16, 185, 129, 0.3);
    }

    /* HIDE DEFAULT ELEMENTS */
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. BACKEND FUNCTIONS
# ==========================================
def get_groq_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
        return Groq(api_key=api_key)
    except Exception:
        st.error("⚠️ API Key missing. Please check secrets.toml")
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
# 4. MAIN UI STRUCTURE
# ==========================================

# HEADER SECTION
st.markdown("""
<div class="main-header">
    <h1>✨ Microstock Metadata AI</h1>
    <p>Generate Titles, Descriptions & Keywords instantly with Llama 4 Vision.</p>
</div>
""", unsafe_allow_html=True)

# CONTROL BAR (CARD STYLE)
with st.container():
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        platform = st.selectbox("🎯 Target Agency", ["Adobe Stock", "Shutterstock", "Getty Images", "Freepik"])
    with col2:
        st.selectbox("🌐 Output Language", ["English (Default)"], disabled=True)
    with col3:
        st.info("💡 **Pro Tip:** Upload high-quality JPGs for best keyword accuracy.")

st.write("") # Spacer

# UPLOAD SECTION
uploaded_files = st.file_uploader(
    "📂 Drop your photos here to start processing (Max 10)", 
    accept_multiple_files=True, 
    type=['png', 'jpg', 'jpeg']
)

# SESSION STATE
if 'results_data' not in st.session_state:
    st.session_state.results_data = []

# START BUTTON
if st.button("🚀 START AI ANALYSIS"):
    if not uploaded_files:
        st.warning("⚠️ Please upload at least one image.")
        st.stop()

    client = get_groq_client()
    st.session_state.results_data = []
    
    progress_bar = st.progress(0, text="Initializing AI Engine...")
    
    # PROCESSING LOOP
    for i, file in enumerate(uploaded_files):
        current_progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(current_progress, text=f"Processing Image {i+1}/{len(uploaded_files)}: {file.name}")
        
        try:
            base64_image = encode_image(file)
            prompt = f"""
            Analyze image for {platform}. Task: Microstock Metadata.
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
            
            # --- HASIL (CARD STYLE) ---
            with st.expander(f"✅ Result: {file.name}", expanded=True):
                c_img, c_data = st.columns([1, 3])
                with c_img:
                    st.image(file, use_container_width=True)
                with c_data:
                    st.text_input("Title", value=p_title, key=f"t_{i}")
                    st.text_area("Description", value=p_desc, height=80, key=f"d_{i}")
                    st.text_area("Keywords", value=p_keys, height=100, key=f"k_{i}")

        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")

    progress_bar.empty()
    st.success("🎉 All files processed successfully!")

# DOWNLOAD SECTION (MODERN FOOTER)
if st.session_state.results_data:
    st.markdown("---")
    st.subheader("📥 Export Your Data")
    
    df = pd.DataFrame(st.session_state.results_data)
    csv = df.to_csv(index=False).encode('utf-8')
    
    col_dl1, col_dl2 = st.columns([1, 2])
    with col_dl1:
        st.download_button(
            label="DOWNLOAD CSV FILE NOW",
            data=csv,
            file_name="microstock_metadata.csv",
            mime="text/csv",
            type="primary"
        )
    with col_dl2:
        st.caption(f"✅ Ready to upload: **{len(df)} files**. Contains Titles, Descriptions, and Keywords.")
        with st.expander("Show Data Preview"):
            st.dataframe(df)
