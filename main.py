import os
import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader

# Page setup
st.set_page_config(page_title="Alpha CISO AI", page_icon="🛡️", layout="wide")
st.title("🛡️ Alpha CISO AI Assistant & Operational Engine")
st.caption("Enterprise Risk Quantification, Remediation & Context-Aware Assistant")

# 1. API KEY SETUP
client = genai.Client(api_key=GEMINI_API_KEY)

# Dynamic System Prompt
DEFAULT_SYSTEM_INSTRUCTION = """You are "Alpha", an enterprise CISO AI Assistant and cybersecurity operational expert.

CRITICAL BEHAVIOR RULES:
1. STRICT INTENT MATCHING:
   - If the user asks a GENERAL CYBERSECURITY QUESTION or CUSTOM QUERY (e.g., "Summarize 2026 attacks", "Explain Zero Trust"), answer directly and comprehensively using your broader cybersecurity knowledge base. DO NOT default to a compliance gap table or state "information not found in document" unless the user explicitly requested data from the document.
   - If the user asks for REMEDIATION, output step-by-step engineering/operational controls.
   - If the user asks for an AUDIT, perform a compliance gap analysis.

2. DOCUMENT CITATION & NAMING:
   - Refer to uploaded documents strictly by the EXACT FILENAMES provided in the prompt header (e.g., "[Company W] Emergency Response Plan v9.5.pdf"). Do NOT rely on internal document titles or metadata IDs.
   - Cite specific pages (e.g., Page 3) when referencing uploaded file content.
"""

if "system_instruction" not in st.session_state:
    st.session_state["system_instruction"] = DEFAULT_SYSTEM_INSTRUCTION
if "model_temperature" not in st.session_state:
    st.session_state["model_temperature"] = 0.2

def extract_pdf_data(uploaded_file):
    """Extracts text and attaches exact desktop filename."""
    if uploaded_file is None:
        return "", ""
    filename = uploaded_file.name
    reader = PdfReader(uploaded_file)
    text = ""
    for idx, page in enumerate(reader.pages):
        extracted = page.extract_text()
        if extracted:
            text += f"\n--- [PAGE {idx + 1}] ---\n" + extracted + "\n"
    return filename, text

# Main Navigation Tabs
tab_auditor, tab_admin = st.tabs(["🛡️ CISO AI Workspace", "⚙️ Admin Prompt Tuning Interface"])

# ==========================================
# TAB 1: CISO AI WORKSPACE
# ==========================================
with tab_auditor:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("1. Upload Context Documents")
        company_pdf = st.file_uploader("Upload Primary Policy / Plan (PDF)", type=["pdf"], key="company_pdf")
        regulatory_pdf = st.file_uploader("Upload Secondary Baseline / Standard (PDF)", type=["pdf"], key="reg_pdf")

    with col2:
        st.subheader("2. Ask CISO AI")
        
        query_type = st.selectbox(
            "Select Operational Task or Custom Prompt:",
            [
                "Custom Query",
                "Technical Remediation Plan",
                "Compliance & Gap Audit",
                "Incident Response Workflow"
            ]
        )
        
        default_prompts = {
            "Custom Query": "",
            "Technical Remediation Plan": "Based on the vulnerabilities in the uploaded primary document, provide a step-by-step technical remediation plan.",
            "Compliance & Gap Audit": "Audit the primary policy against the secondary regulatory standard. Highlight specific non-compliant clauses.",
            "Incident Response Workflow": "Detail the operational containment and notification steps required under this policy."
        }
        
        user_query = st.text_area(
            "Prompt Input:", 
            value=default_prompts[query_type], 
            height=120
        )
        
        if st.button("Run Alpha AI Execution", type="primary"):
            if not user_query.strip():
                st.warning("Please enter a query prompt before running.")
            else:
                with st.spinner("Processing prompt..."):
                    comp_name, comp_text = extract_pdf_data(company_pdf)
                    reg_name, reg_text = extract_pdf_data(regulatory_pdf)
                    
                    context_block = ""
                    if comp_text:
                        context_block += f"\n=== PRIMARY UPLOADED FILE NAME: '{comp_name}' ===\n{comp_text[:50000]}\n"
                    if reg_text:
                        context_block += f"\n=== SECONDARY UPLOADED FILE NAME: '{reg_name}' ===\n{reg_text[:50000]}\n"
                    
                    if context_block:
                        full_prompt = (
                            f"{context_block}\n"
                            f"===============================\n"
                            f"USER INSTRUCTION: {user_query}\n\n"
                            f"NOTE: If the request is a general question, answer it directly using general domain knowledge while citing attached files '{comp_name}' or '{reg_name}' only if relevant."
                        )
                    else:
                        full_prompt = user_query

                    try:
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=full_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=st.session_state["system_instruction"],
                                temperature=st.session_state["model_temperature"],
                            )
                        )
                        st.markdown("### 📊 Alpha Response")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Error generating response: {e}")

# ==========================================
# TAB 2: ADMIN PROMPT TUNING INTERFACE
# ==========================================
with tab_admin:
    st.subheader("⚙️ Fine-Tune System Behavior & Parameters")
    
    admin_system_prompt = st.text_area(
        "Edit System Instruction:",
        value=st.session_state["system_instruction"],
        height=300
    )
    
    admin_temp = st.slider(
        "Model Temperature:",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state["model_temperature"],
        step=0.05
    )
    
    col_admin_a, col_admin_b = st.columns([1, 4])
    with col_admin_a:
        if st.button("Save Configuration", type="primary"):
            st.session_state["system_instruction"] = admin_system_prompt
            st.session_state["model_temperature"] = admin_temp
            st.success("Updated system parameters!")
            
    with col_admin_b:
        if st.button("Reset Settings"):
            st.session_state["system_instruction"] = DEFAULT_SYSTEM_INSTRUCTION
            st.session_state["model_temperature"] = 0.2
            st.info("Reset to defaults.")
