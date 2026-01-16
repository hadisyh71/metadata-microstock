import streamlit as st
from groq import Groq
import base64
import pandas as pd

# ==========================================
# 1. PAGE CONFIGURATION (FIXED SIDEBAR)
# ==========================================
st.set_page_config(
    page_title="Microstock Metadata AI",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"  # << FORCE SIDEBAR OPEN DEFAULT
)

# ==========================================
# 2. CSS STYLING (CLEAN WHITE & VISIBLE BUTTONS)
# ==========================================
st.markdown("""
    <style>
    /* 1. Force Clean White Background */
    .stApp {
        background-color: #FFFFFF;
        color: #111827;
    }
    
    /* 2. Sidebar Styling (Light Grey) */
    [data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E5E7EB;
    }

    /* 3. FIX: Make the Sidebar Toggle Button VISIBLE (Black) */
    [data-testid="collapsedControl"] {
        color: #000000 !important;
        background-color: #E5E7EB !important;
        border-radius: 5px;
        display: block !important;
    }
    
    /* 4. Headers & Text */
    h1, h2, h3 {
        color: #111827 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* 5. Professional Blue Buttons */
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        width: 100%;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        color: white;
    }
    
    /* 6. Inputs & Text Areas */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea textarea {
        background-color: #FFFFFF;
        color: #111827;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
    }
    
    /* 7. Hide Streamlit Branding */
    #MainMenu, footer, header {visibility: hidden;}
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
        st.error("⚠️ API Key missing in secrets.toml")
        st.stop()

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def parse_ai_response(text):
    """Simple parser to extract data for CSV"""
    title, desc, keys = "", "", ""
    try:
        lines = text.split('\n')
        for line in lines:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                desc = line.replace("DESCRIPTION:", "").strip()
            elif line.startswith("KEYWORDS:"):
                keys = line.replace("KEYWORDS:", "").strip()
        
        # Fallback if multiline
        if not title and "TITLE:" in text:
            parts = text.split("TITLE:")[1].split("DESCRIPTION:")
            title = parts[0].strip()
            if "KEYWORDS:" in parts[1]:
                d_parts = parts[1].split("KEYWORDS:")
                desc = d_parts[0].strip()
                keys = d_parts[1].strip()
    except:
        pass
    return title, desc, keys

# ==========================================
# 4. SIDEBAR (ENGLISH UI)
# ==========================================
with st.sidebar:
    st.header("⚙️ Settings")
    
    platform = st.selectbox("Target Agency:", ("Adobe Stock", "Shutterstock", "Freepik", "Getty Images"))
    # Hardcoded to English output as requested
    st.caption("Output Language: **English (Default)**")
    
    st.divider()
    st.caption("Engine: **Llama 4 Scout**")
    st.info("ℹ️ **CSV Feature:** Download button will appear after processing.")

# ==========================================
# 5. MAIN INTERFACE (ENGLISH UI)
# ==========================================
st.title("📸 Microstock Metadata AI")
st.write("Generate optimized **Titles, Descriptions, & Keywords** and export to **CSV**.")

# Upload Area
uploaded_files = st.file_uploader(
    "📂 Upload your photos here (Max 10 Files)", 
    accept_multiple_files=True, 
    type=['png', 'jpg', 'jpeg']
)

# Session State for CSV Data
if 'results_data' not in st.session_state:
    st.session_state.results_data = []

# Process Button
if st.button("🚀 GENERATE METADATA"):
    
    if not uploaded_files:
        st.warning("⚠️ Please upload images first.")
        st.stop()

    client = get_groq_client()
    st.session_state.results_data = [] # Reset previous data
    
    progress_bar = st.progress(0, text="Starting analysis...")
    
    for i, file in enumerate(uploaded_files):
        current_progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(current_progress, text=f"Processing: {file.name}")
        
        try:
            base64_image = encode_image(file)
            
            # Prompt forces English Output
            prompt = f"""
            Analyze this image for {platform}. 
            Task: Create metadata strictly in English.
            Output Format (Plain Text only, NO Markdown):
            
            TITLE: [Commercial, SEO-friendly title, max 70 chars]
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
            
            # Parse for CSV
            p_title, p_desc, p_keys = parse_ai_response(result_text)
            
            st.session_state.results_data.append({
                "Filename": file.name,
                "Title": p_title,
                "Description": p_desc,
                "Keywords": p_keys
            })
            
            # Display Result
            with st.expander(f"✅ Result: {file.name}", expanded=False):
                col_img, col_res = st.columns([1, 2])
                with col_img: st.image(file, use_container_width=True)
                with col_res: st.text_area("Metadata:", value=result_text, height=200)
                
        except Exception as e:
            st.error(f"Failed to process {file.name}: {e}")

    progress_bar.progress(1.0, text="✅ All Done!")
    st.success("Analysis Complete!")

# ==========================================
# 6. CSV DOWNLOAD SECTION
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
            file_name="microstock_metadata.csv",
            mime="text/csv",
            type="primary"
        )
    with col2:
        with st.expander("🔍 Preview Data Table"):
            st.dataframe(df)
