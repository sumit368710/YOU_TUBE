import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from deep_translator import GoogleTranslator
from fpdf import FPDF
import yt_dlp

from youtube_transcript_api import YouTubeTranscriptApi
# import yt_dlp
import re

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="YouTube Chatbot",
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
# CUSTOM CSS
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
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import re


def get_video_id(url):
    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?&]+)",
        r"shorts/([^?&]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


# def extract_video_info(url):
#     try:
#         ydl_opts = {
#             "quiet": True,
#             "extract_flat": False,
#             "skip_download": True
#         }

#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(url, download=False)

#         title = info.get("title", "")
#         description = info.get("description", "")
#         channel = info.get("uploader", "")
#         duration = info.get("duration_string", "")
#         views = info.get("view_count", "")
#         upload_date = info.get("upload_date", "")
#         tags = info.get("tags", [])

#         # ===== GET TRANSCRIPT =====
#         transcript_text = ""
#         video_id = get_video_id(url)

#         if video_id:
#             try:
#                 transcript = YouTubeTranscriptApi.get_transcript(video_id)

#                 transcript_text = " ".join(
#                     [item["text"] for item in transcript]
#                 )

#             except:
#                 transcript_text = "Transcript not available."

#         data = f"""
# Title: {title}

# Channel: {channel}

# Duration: {duration}

# Views: {views}

# Upload Date: {upload_date}

# Tags: {', '.join(tags[:15])}

# Description:
# {description}

# Transcript:
# {transcript_text}
# """
#         return data

#     except Exception as e:
#         return f"Error: {str(e)}"

def extract_video_info(url):
    try:
        video_id = get_video_id(url)

        if not video_id:
            return "Error: Invalid YouTube URL"

        # ===== GET TRANSCRIPT =====
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)

            transcript_text = " ".join(
                [item["text"] for item in transcript]
            )

        except:
            transcript_text = "Transcript not available."

        # ===== BASIC INFO (NO yt-dlp) =====
        data = f"""
Video ID: {video_id}

Transcript:
{transcript_text}
"""
        return data

    except Exception as e:
        return f"Error: {str(e)}"


# def summarize_video(video_text):
#     prompt = f"""
# You are an expert teacher, examiner, and educational content writer.

# Convert the given YouTube video topic/content into PROFESSIONAL STUDY NOTES with BEAUTIFUL formatting.

# Video Content:
# {video_text}

# Instructions:
# - If transcript exists, use it fully.
# - If transcript not available, infer intelligently from topic/title.
# - Use simple language.
# - Make content detailed, exam-ready, and professional.
# - VERY IMPORTANT: Questions and answers must be on separate lines.
# - Never write question and answer in same line.
# - Use proper spacing.
# - Use markdown formatting.

# Use this exact format:

# # 1. Chapter / Topic Introduction
# (Paragraph explanation)

# # 2. Full Detailed Notes
# (Headings + subheadings + bullet points)

# # 3. Important Definitions
# - Term:
#   Definition:

# # 4. Important Points for Exam
# - Point 1
# - Point 2

# # 5. Short Questions with Answers

# ## Q1. What is ...?
# **Answer:**
# (write answer below)

# ## Q2. Who is ...?
# **Answer:**
# (write answer below)

# (Create minimum 5)

# # 6. Long Questions with Answers

# ## Q1. Explain ...
# **Answer:**
# (detailed answer below)

# (Create minimum 5)

# # 7. Multiple Choice Questions (MCQs)

# ## Q1. ....
# a) ...
# b) ...
# c) ...
# d) ...

# **Correct Answer:** b)

# (Create minimum 10)

# # 8. True / False

# 1. Statement here  
# **Answer:** True

# (Create minimum 5)

# # 9. One Word Answers

# 1. Question:
# **Answer:** ....

# (Create minimum 5)

# # 10. Revision Summary
# (Bullets)

# # 11. Real Life Importance / Applications
# (Paragraph)

# # 12. Final Conclusion
# (Paragraph)

# Rules:
# - Separate every question and answer clearly.
# - Use headings.
# - Add spacing between sections.
# - Make UI look clean when shown in Streamlit.
# - No one-line mixed answers.

# Now generate professional formatted output.
# """
#     response = model.invoke(prompt)
#     return response.content


# def answer_question(video_text, summary, question):
#     prompt = f"""
# You are an expert assistant answering questions about a YouTube video.

# Use ONLY the provided video transcript, metadata, and summary.

# VIDEO CONTENT:
# {video_text}

# VIDEO SUMMARY:
# {summary}

# USER QUESTION:
# {question}

# Instructions:
# - Answer only using information from the video.
# - If the creator explained steps, list them clearly.
# - If the user asks "what did he say about X", extract that part.
# - If the user asks for examples, provide examples mentioned in video.
# - If timeline/order matters, explain in sequence.
# - Be concise but complete.
# - If the answer is not present in the video, reply:
#   "This was not clearly mentioned in the video."

# Output:
# Give a clean direct answer.
# """
#     response = model.invoke(prompt)
#     return response.content

def summarize_video(video_text):

    # 🚫 HARD CHECK (prevent hallucination)
    if not video_text or len(video_text.strip()) < 50 or "Transcript not available" in video_text:
        return "❌ Transcript not available for this video. Please try another video."

    prompt = f"""
You are a highly experienced TEACHER who explains concepts clearly to students.

Your job is to convert the YouTube video content into structured STUDY NOTES.

STRICT RULES (VERY IMPORTANT):
- Use ONLY the given video content
- DO NOT guess or add outside knowledge
- DO NOT change topic
- If something is unclear → skip it
- Explain like a teacher teaching in classroom
- Keep explanations simple, clear, and structured

VIDEO CONTENT:
{video_text}

OUTPUT FORMAT:

# 1. Chapter / Topic Introduction
Explain what this video is about in simple terms like a teacher introducing a topic.

# 2. Full Detailed Notes
- Use headings and subheadings
- Break into concepts
- Explain step-by-step like teaching students
- Use bullet points wherever needed

# 3. Important Definitions
- Term:
  Definition:

# 4. Important Points for Exam
- Key takeaway points
- Focus on what students should remember

# 5. Short Questions with Answers

## Q1. ...
**Answer:**
(clear explanation below)

(Create at least 5)

# 6. Long Questions with Answers

## Q1. ...
**Answer:**
(detailed explanation like exam answer)

(Create at least 5)

# 7. Multiple Choice Questions (MCQs)

## Q1. ...
a) ...
b) ...
c) ...
d) ...

**Correct Answer:** ...

(Create at least 5)

# 8. True / False

1. Statement  
**Answer:** True/False

(Create at least 5)

# 9. One Word Answers

1. Question:
**Answer:** ...

(Create at least 5)

# 10. Revision Summary
- Short bullet revision points

# 11. Real Life Importance / Applications
Explain how this topic is useful in real life.

# 12. Final Conclusion
Summarize like a teacher concluding the lecture.

FINAL INSTRUCTION:
- Maintain clean formatting
- Separate every question and answer
- No mixing in one line
- Make it look like proper study notes

Now generate the output.
"""

    response = model.invoke(prompt)
    return response.content

def answer_question(video_text, summary, question):

    prompt = f"""
You are a teacher answering student questions based ONLY on a YouTube video.

STRICT RULES:
- Answer ONLY from given video content
- DO NOT guess
- DO NOT add external knowledge
- If not found → say clearly

VIDEO CONTENT:
{video_text}

VIDEO SUMMARY:
{summary}

STUDENT QUESTION:
{question}

INSTRUCTIONS:
- Answer clearly like a teacher
- If explanation needed → explain step-by-step
- Keep it simple and understandable
- If answer not present in video:
  "This was not clearly mentioned in the video."

OUTPUT:
Give a clear, structured answer.
"""

    response = model.invoke(prompt)
    return response.content


def translate_text(text, lang):
    try:
        translator = GoogleTranslator(source="auto", target=lang)
        return translator.translate(text)
    except:
        return text


def clean_text(text):
    return text.encode("latin-1", "ignore").decode("latin-1")


def create_pdf(summary, chats):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "YouTube Chat Report", ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, clean_text(summary))
    pdf.ln(6)

    if chats:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Questions & Answers", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", "", 12)

        for msg in chats:
            role = msg["role"]
            text = msg["content"]

            if role == "user":
                pdf.multi_cell(0, 8, clean_text("Q: " + text))
            else:
                pdf.multi_cell(0, 8, clean_text("A: " + text))

            pdf.ln(2)

    path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    pdf.output(path)
    return path

# ==================================================
# SESSION
# ==================================================
if "video_loaded" not in st.session_state:
    st.session_state.video_loaded = False

if "video_data" not in st.session_state:
    st.session_state.video_data = ""

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

# ==================================================
# SIDEBAR
# ==================================================
st.sidebar.title("⚙ Settings")

language = st.sidebar.selectbox(
    "Select Language",
    ["English", "Hindi", "Spanish", "French"]
)

if st.sidebar.button("🗑 Clear Chat"):
    st.session_state.video_loaded = False
    st.session_state.video_data = ""
    st.session_state.summary = ""
    st.session_state.messages = []
    st.rerun()

# ==================================================
# HEADER
# ==================================================
st.title("🎥 YouTube Chatbot")

# ==================================================
# URL INPUT
# ==================================================
url = st.text_input("Paste YouTube Link")

if st.button("🚀 Generate Summary"):

    if url.strip() == "":
        st.warning("Please enter URL")
        st.stop()

    with st.spinner("Fetching video..."):
        video_data = extract_video_info(url)

    if "Error:" in video_data:
        st.error(video_data)
        st.stop()

    with st.spinner("Generating summary..."):
        summary = summarize_video(video_data)

    if language != "English":
        lang_code = {
            "Hindi":"hi",
            "Spanish":"es",
            "French":"fr"
        }[language]

        summary = translate_text(summary, lang_code)

    st.session_state.video_loaded = True
    st.session_state.video_data = video_data
    st.session_state.summary = summary
    st.session_state.messages = []

    st.session_state.messages.append({
        "role":"assistant",
        "content":summary
    })

    st.rerun()

# ==================================================
# CHAT HISTORY
# ==================================================
for msg in st.session_state.messages:

    if msg["role"] == "user":
        st.markdown(
            f"<div class='user-box'>{msg['content']}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='bot-box'>{msg['content']}</div>",
            unsafe_allow_html=True
        )

# ==================================================
# PDF
# ==================================================
if st.session_state.video_loaded:

    pdf = create_pdf(
        st.session_state.summary,
        st.session_state.messages
    )

    with open(pdf, "rb") as f:
        st.download_button(
            "📄 Download PDF",
            data=f,
            file_name="youtube_chat.pdf",
            mime="application/pdf"
        )

# ==================================================
# CHAT INPUT (BOTTOM LIKE CHATGPT)
# ==================================================
if st.session_state.video_loaded:

    question = st.chat_input("Ask about this video...")

    if question:

        st.session_state.messages.append({
            "role":"user",
            "content":question
        })

        with st.spinner("Thinking..."):
            answer = answer_question(
                st.session_state.video_data,
                st.session_state.summary,
                question
            )

        if language != "English":
            lang_code = {
                "Hindi":"hi",
                "Spanish":"es",
                "French":"fr"
            }[language]

            answer = translate_text(answer, lang_code)

        st.session_state.messages.append({
            "role":"assistant",
            "content":answer
        })

        st.rerun()