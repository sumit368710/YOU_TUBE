import streamlit as st
import os
import tempfile
import requests
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from deep_translator import GoogleTranslator
from fpdf import FPDF
from youtube_transcript_api import YouTubeTranscriptApi
import re

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="YouTube Teacher",
    page_icon="🎥",
    layout="centered"
)

# ==================================================
# LOAD ENV
# ==================================================
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# ==================================================
# MODEL
# ==================================================
model = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=groq_api_key,
    temperature=0.3
)

# ==================================================
# CSS
# ==================================================
st.markdown("""
<style>

/* APP */
.stApp{
    background:#0f172a;
    color:white;
}

/* MOBILE CENTER */
.block-container{
    max-width:430px;
    margin:auto;
    padding-top:10px;
    padding-bottom:110px;
}

/* Hide Streamlit */
footer {visibility:hidden;}
#MainMenu {visibility:hidden;}

/* Title */
h1,h2,h3{
    text-align:center;
    color:white;
}

/* Inputs */
.stTextInput input{
    background:#1e293b;
    color:white;
    border:1px solid #334155;
    border-radius:18px;
    padding:14px;
}

/* Buttons */
.stButton button{
    width:100%;
    height:46px;
    border:none;
    border-radius:18px;
    background:linear-gradient(90deg,#2563eb,#7c3aed);
    color:white;
    font-weight:600;
}

/* Chat bubbles */
.user-box{
    background:#2563eb;
    color:white;
    padding:12px 14px;
    border-radius:18px 18px 4px 18px;
    margin:8px 0;
    width:fit-content;
    max-width:85%;
    margin-left:auto;
}

.bot-box{
    background:#1e293b;
    color:white;
    padding:12px 14px;
    border-radius:18px 18px 18px 4px;
    margin:8px 0;
    width:fit-content;
    max-width:85%;
}

/* Sidebar */
section[data-testid="stSidebar"]{
    background:#111827;
}

/* Chat input full width same as Generate Summary button */
[data-testid="stChatInput"]{
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100%;
    max-width: 430px;   /* same as main container */
    background: #0f172a;
    padding: 12px;
    border-top: 1px solid #334155;
    z-index: 999;
}

/* Mobile responsive */
@media (max-width: 768px){
[data-testid="stChatInput"]{
    max-width: 100%;
    left: 0;
    transform: none;
}
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# FUNCTIONS
# ==================================================
def get_video_id(url):
    patterns = [r"v=([^&]+)", r"youtu\.be/([^?&]+)", r"shorts/([^?&]+)"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# def extract_video_info(url):
#     try:
#         video_id = get_video_id(url)
#         if not video_id:
#             return "Error: Invalid URL"

#         # ===== TRY TRANSCRIPT =====
#         transcript_text = ""
#         try:
#             transcript = YouTubeTranscriptApi.get_transcript(video_id)
#             transcript_text = " ".join([i["text"] for i in transcript])
#         except:
#             transcript_text = ""

#         # ===== GET TITLE =====
#         title = ""
#         try:
#             res = requests.get(
#                 f"https://www.youtube.com/oembed?url={url}&format=json"
#             )
#             title = res.json().get("title", "")
#         except:
#             pass

#         if transcript_text:
#             return f"Title: {title}\n\nTranscript:\n{transcript_text}"
#         elif title:
#             return f"Title: {title}\n\nTranscript not available."
#         else:
#             return "Error: Could not fetch data"

#     except Exception as e:
#         return f"Error: {str(e)}"

def extract_video_info(url):
    try:
        video_id = get_video_id(url)

        if not video_id:
            return "Error: Invalid URL"

        # ===== TRY TRANSCRIPT =====
        transcript_text = ""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([i["text"] for i in transcript])
        except:
            transcript_text = ""

        # ===== ALWAYS GET TITLE =====
        title = ""
        try:
            res = requests.get(
                f"https://www.youtube.com/oembed?url={url}&format=json"
            )
            title = res.json().get("title", "")
        except:
            pass

        # ===== NEVER RETURN EMPTY =====
        if transcript_text:
            return f"Title: {title}\n\nTranscript:\n{transcript_text}"
        else:
            return f"Title: {title}\n\nNOTE: Transcript not available."

    except Exception as e:
        return f"Error: {str(e)}"


def summarize_video(video_text):

    if not video_text:
        return "❌ Unable to process video."

    prompt = f"""
You are a PROFESSOR OF LAW teaching students for judiciary exams, UPSC, and law school.

Your job is to convert the YouTube video into HIGH-QUALITY LEGAL STUDY NOTES.

========================
STRICT RULES
========================
1. IF transcript exists:
   - Use ONLY the video content
   - Do NOT add outside legal facts

2. IF transcript is NOT available:
   - Use GENERAL LEGAL KNOWLEDGE
   - Clearly mention:
     "Note: This is a general legal explanation as transcript is unavailable."

3. Always stay within LEGAL CONTEXT
4. Do NOT include unrelated topics (e.g., Machine Learning, coding, etc.)
5. Content must be exam-oriented (UPSC, Judiciary, CLAT)
6. Write like a LAW PROFESSOR explaining in class

7. IF transcript is available:
→ generate detailed legal notes

8. IF transcript is NOT available:
→ generate GENERAL legal explanation based on title
→ clearly mention it's general explanation
→ DO NOT hallucinate specific facts

========================
VIDEO DATA:
{video_text}
========================

OUTPUT FORMAT:

# 1. Topic Introduction
- Explain the legal topic clearly and formally

# 2. Constitutional / Legal Background
- Relevant Articles, Acts, or Provisions (if applicable)

# 3. Detailed Explanation
- Break into concepts
- Explain like teaching law students

# 4. Powers, Functions, or Features (if applicable)
- Structured bullet points

# 5. Important Legal Definitions
- Term:
  Definition:

# 6. Landmark Cases / Examples (if relevant)
- Case name + explanation

# 7. Important Points for Exams
- Key takeaways for revision

# 8. Short Questions (Law Based)

## Q1.
**Answer:**

(Create 5 – strictly legal questions only)

# 9. Long Questions (Law Based)

## Q1.
**Answer:**

(Create 5 – descriptive, exam-style)

# 10. MCQs (Law Based)

## Q1.
a)
b)
c)
d)

**Correct Answer:**

(Create 5)

# 11. Conclusion
- Summarize like a law professor

========================
FINAL INSTRUCTION:
- Maintain professional legal tone
- Keep formatting clean
- No unrelated topics
- No hallucination
========================
"""

    response = model.invoke(prompt)
    return response.content


def answer_question(video_text, summary, question):

    prompt = f"""
You are a LAW PROFESSOR answering student queries.

========================
STRICT RULES
========================

IF transcript exists:
- Answer ONLY from video content
- Do NOT add external legal knowledge

IF transcript NOT available:
- Answer using GENERAL LEGAL KNOWLEDGE
- Clearly say:
  "This is a general legal explanation as transcript is unavailable."

- Do NOT answer non-legal questions
- Keep answers relevant to LAW only

========================
VIDEO CONTENT:
{video_text}

SUMMARY:
{summary}

STUDENT QUESTION:
{question}
========================

INSTRUCTIONS:
- Answer like a law professor
- Use clear legal reasoning
- Use examples if needed
- If question is unrelated to law → say:
  "This question is not relevant to the legal topic."

- If answer not found → say clearly

========================
OUTPUT:
Give a structured legal answer.
========================
"""

    response = model.invoke(prompt)
    return response.content


def translate_text(text, lang):
    try:
        return GoogleTranslator(source="auto", target=lang).translate(text)
    except:
        return text


def clean_text(text):
    return text.encode("latin-1", "ignore").decode("latin-1")


def create_pdf(summary, chats):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "YouTube Study Notes", ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, clean_text(summary))

    for msg in chats:
        role = msg["role"]
        text = msg["content"]
        pdf.ln(2)
        if role == "user":
            pdf.multi_cell(0, 8, clean_text("Q: " + text))
        else:
            pdf.multi_cell(0, 8, clean_text("A: " + text))

    path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    pdf.output(path)
    return path

# ==================================================
# SESSION
# ==================================================
if "video_loaded" not in st.session_state:
    st.session_state.video_loaded = False
    st.session_state.messages = []

# ==================================================
# SIDEBAR
# ==================================================
st.sidebar.title("Settings")

language = st.sidebar.selectbox(
    "Language",
    ["English", "Hindi", "Spanish", "French"]
)

if st.sidebar.button("Clear"):
    st.session_state.video_loaded = False
    st.session_state.messages = []
    st.rerun()

# ==================================================
# UI
# ==================================================
st.title("🎥 YouTube Teacher")

url = st.text_input("Paste YouTube Link")

if st.button("Generate Summary"):

    with st.spinner("Processing..."):
        video_data = extract_video_info(url)

    if "Error" in video_data:
        st.error(video_data)
        st.stop()

    summary = summarize_video(video_data)

    if language != "English":
        code = {"Hindi":"hi","Spanish":"es","French":"fr"}[language]
        summary = translate_text(summary, code)

    st.session_state.video_loaded = True
    st.session_state.video_data = video_data
    st.session_state.summary = summary
    st.session_state.messages = [{"role":"assistant","content":summary}]
    st.rerun()

# ==================================================
# CHAT DISPLAY
# ==================================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-box'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-box'>{msg['content']}</div>", unsafe_allow_html=True)

# ==================================================
# PDF
# ==================================================
if st.session_state.video_loaded:
    pdf = create_pdf(st.session_state.summary, st.session_state.messages)
    with open(pdf, "rb") as f:
        st.download_button("Download PDF", f, "notes.pdf")

# ==================================================
# CHAT INPUT
# ==================================================
if st.session_state.video_loaded:
    question = st.chat_input("Ask anything...")

    if question:
        st.session_state.messages.append({"role":"user","content":question})

        answer = answer_question(
            st.session_state.video_data,
            st.session_state.summary,
            question
        )

        if language != "English":
            code = {"Hindi":"hi","Spanish":"es","French":"fr"}[language]
            answer = translate_text(answer, code)

        st.session_state.messages.append({"role":"assistant","content":answer})
        st.rerun()