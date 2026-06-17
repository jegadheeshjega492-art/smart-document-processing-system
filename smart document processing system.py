import streamlit as st
import sqlite3
import pdfplumber
import re
import json
import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
import pyotp
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─────────────────────────────────────────────
# CREDENTIALS
# ─────────────────────────────────────────────
USERNAME = "jegadheeshjega492@gmail.com"
DEFAULT_PASSWORD = "Jega@2003"

# ── Gmail SMTP Config ──
GMAIL_USER = "jegadheeshjega492@gmail.com"
GMAIL_APP_PASSWORD = "glzk dmnp yrnq obos"

PWD_FILE = "current_password.txt"
if not os.path.exists(PWD_FILE):
    with open(PWD_FILE, "w") as f:
        f.write(DEFAULT_PASSWORD)

def get_password():
    with open(PWD_FILE, "r") as f:
        return f.read().strip()

def save_password(new_pwd):
    with open(PWD_FILE, "w") as f:
        f.write(new_pwd)

# ─────────────────────────────────────────────
# OTP FUNCTIONS
# ─────────────────────────────────────────────
OTP_SECRET_FILE = "otp_secret.txt"
if not os.path.exists(OTP_SECRET_FILE):
    with open(OTP_SECRET_FILE, "w") as f:
        f.write(pyotp.random_base32())
with open(OTP_SECRET_FILE, "r") as f:
    OTP_SECRET = f.read().strip()

def generate_otp():
    totp = pyotp.TOTP(OTP_SECRET, interval=120)
    otp = totp.now()

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_USER
        msg["To"] = USERNAME
        msg["Subject"] = "🔐 Password Reset OTP - AI Document Analyzer"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 30px;">
            <div style="max-width: 480px; margin: auto; background: white;
                        border-radius: 10px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">🔐 Password Reset OTP</h2>
                <p style="color: #555;">Use the OTP below to reset your password for <b>AI Document Analyzer</b>.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px;
                                 color: #1a73e8; background: #e8f0fe; padding: 12px 24px;
                                 border-radius: 8px;">{otp}</span>
                </div>
                <p style="color: #888; font-size: 13px;">⏱️ Valid for <b>2 minutes</b> only.</p>
                <p style="color: #888; font-size: 13px;">If you didn't request this, ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #aaa; font-size: 11px; text-align: center;">AI Document Analyzer</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        print(f"✅ OTP sent to {USERNAME}")

    except Exception as e:
        print(f"❌ Email failed: {e}")
        print(f"OTP (terminal fallback): {otp}")

    return otp

def verify_otp(entered_otp):
    totp = pyotp.TOTP(OTP_SECRET, interval=120)
    return totp.verify(entered_otp, valid_window=1)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="AI Document Analyzer", layout="wide")

for key in ["login", "show_forgot", "otp_sent", "otp_verified"]:
    if key not in st.session_state:
        st.session_state[key] = False

if "otp_timer" not in st.session_state:
    st.session_state.otp_timer = 0

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
if not st.session_state.login:
    st.title("🔐 AI Document Analyzer")
    st.markdown("---")

    if not st.session_state.show_forgot:
        st.subheader("Login")
        user = st.text_input("Username / Email")
        pwd = st.text_input("Password", type="password")

        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("Login", use_container_width=True):
                if user == USERNAME and pwd == get_password():
                    st.session_state.login = True
                    st.rerun()
                else:
                    st.error("❌ Invalid Credentials")
        with col2:
            if st.button("Forgot Password?", use_container_width=True):
                st.session_state.show_forgot = True
                st.session_state.otp_sent = False
                st.session_state.otp_verified = False
                st.rerun()

    else:
        st.subheader("🔁 Reset Password via OTP")
        st.markdown("---")

        if not st.session_state.otp_sent:
            st.info(f"OTP will be sent to your registered email: **{USERNAME}**")

            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("📧 Send OTP", use_container_width=True):
                    with st.spinner("Sending OTP to your Gmail..."):
                        generate_otp()
                    st.session_state.otp_sent = True
                    st.session_state.otp_timer = time.time()
                    st.success(f"✅ OTP sent to {USERNAME}! Check your inbox.")
                    st.rerun()
            with col2:
                if st.button("← Back to Login", use_container_width=True):
                    st.session_state.show_forgot = False
                    st.rerun()

        elif st.session_state.otp_sent and not st.session_state.otp_verified:
            elapsed = time.time() - st.session_state.otp_timer
            remaining = max(0, 120 - int(elapsed))

            if remaining > 0:
                st.info(f"⏱️ OTP valid for **{remaining} seconds** | Check **{USERNAME}** inbox")
            else:
                st.error("⌛ OTP expired! Please resend.")

            otp_input = st.text_input("Enter 6-digit OTP", max_chars=6, placeholder="123456")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Verify OTP", use_container_width=True):
                    if remaining <= 0:
                        st.error("⌛ OTP expired! Click Resend OTP.")
                    elif verify_otp(otp_input.strip()):
                        st.session_state.otp_verified = True
                        st.success("✅ OTP verified!")
                        st.rerun()
                    else:
                        st.error("❌ Wrong OTP! Try again.")
            with col2:
                if st.button("🔄 Resend OTP", use_container_width=True):
                    with st.spinner("Resending OTP..."):
                        generate_otp()
                    st.session_state.otp_timer = time.time()
                    st.success(f"✅ New OTP sent to {USERNAME}!")
                    st.rerun()
            with col3:
                if st.button("← Back", use_container_width=True):
                    st.session_state.show_forgot = False
                    st.session_state.otp_sent = False
                    st.rerun()

        elif st.session_state.otp_verified:
            st.success("✅ OTP Verified! Set your new password.")
            new_pwd = st.text_input("🔒 New Password", type="password")
            confirm_pwd = st.text_input("🔒 Confirm New Password", type="password")

            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("Reset Password", use_container_width=True):
                    if not new_pwd:
                        st.warning("⚠️ Password cannot be empty!")
                    elif len(new_pwd) < 6:
                        st.warning("⚠️ Minimum 6 characters required!")
                    elif new_pwd != confirm_pwd:
                        st.error("❌ Passwords don't match!")
                    else:
                        save_password(new_pwd)
                        st.session_state.show_forgot = False
                        st.session_state.otp_sent = False
                        st.session_state.otp_verified = False
                        st.success("✅ Password reset successful!")
                        st.balloons()
                        st.rerun()
            with col2:
                if st.button("← Back to Login", use_container_width=True):
                    st.session_state.show_forgot = False
                    st.session_state.otp_sent = False
                    st.session_state.otp_verified = False
                    st.rerun()

    st.stop()

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
conn = sqlite3.connect("documents.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS documents(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    content TEXT
)
""")
conn.commit()

# ─────────────────────────────────────────────
# OCR
# ─────────────────────────────────────────────
@st.cache_resource
def load_ocr():
    return PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

ocr = load_ocr()

def extract_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

def preprocess_image(img):
    img_np = np.array(img)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return thresh

def extract_image(img):
    processed = preprocess_image(img)
    result = ocr.ocr(processed)
    text = []
    for line in result:
        if line:
            for word in line:
                text.append(word[1][0])
    return " ".join(text)

# ─────────────────────────────────────────────
# CLASSIFY
# ─────────────────────────────────────────────
def classify_document(text):
    txt = text.upper()
    if any(k in txt for k in ["UNIQUE IDENTIFICATION AUTHORITY", "AADHAAR", "UIDAI"]):
        return "AADHAAR"
    elif any(k in txt for k in ["BIRTH CERTIFICATE", "PLACE OF BIRTH", "BORN ON", "MUNICIPAL CORPORATION", "GRAM PANCHAYAT"]) and "RESUME" not in txt:
        return "BIRTH_CERTIFICATE"
    elif any(k in txt for k in ["BONAFIDE", "BONA FIDE", "BONAFIED"]) and "TRANSFER" not in txt:
        return "BONAFIDE"
    elif any(k in txt for k in ["TRANSFER CERTIFICATE", "T.C.", "TC NO", "LEAVING CERTIFICATE"]):
        return "TRANSFER_CERTIFICATE"
    elif any(k in txt for k in ["MARK SHEET", "MARKSHEET", "GRADE SHEET", "CGPA", "SGPA", "PERCENTAGE", "SEMESTER"]) and "RESUME" not in txt:
        return "MARKSHEET"
    elif any(k in txt for k in [
            "OFFER LETTER", "WE ARE PLEASED TO OFFER", "APPOINTMENT LETTER",
            "WE ARE EXCITED TO OFFER", "PLEASED TO INFORM", "HAPPY TO OFFER",
            "OFFER YOU THE POSITION", "OFFERED THE POSITION",
            "POSITION OF INTERN", "JOINING DATE", "TERMS AND CONDITIONS OF YOUR EMPLOYMENT",
            "THIS IS TO OFFER", "SALARY OFFERED", "CTC", "COST TO COMPANY"]):
        return "OFFER_LETTER"
    elif any(k in txt for k in ["INTERNSHIP CERTIFICATE", "INTERN CERTIFICATE",
                                  "SUCCESSFULLY COMPLETED", "COMPLETION CERTIFICATE",
                                  "HAS SUCCESSFULLY COMPLETED", "HAS COMPLETED THE INTERNSHIP",
                                  "CERTIFICATE OF INTERNSHIP", "THIS IS TO CERTIFY"]):
        return "INTERNSHIP_CERTIFICATE"
    elif any(k in txt for k in ["INVOICE", "BILL NO", "GSTIN", "TAX INVOICE"]):
        return "INVOICE"
    elif any(k in txt for k in ["RESUME", "CURRICULUM VITAE", "OBJECTIVE", "SKILLS", "PROJECTS", "EXPERIENCE"]):
        return "RESUME"
    return "UNKNOWN"

# ─────────────────────────────────────────────
# KNOWN LISTS
# ─────────────────────────────────────────────
INDIA_STATES = [
    "Tamil Nadu", "Andhra Pradesh", "Telangana", "Karnataka", "Kerala",
    "Maharashtra", "Gujarat", "Rajasthan", "Uttar Pradesh", "Bihar",
    "West Bengal", "Odisha", "Madhya Pradesh", "Punjab", "Haryana",
    "Jharkhand", "Chhattisgarh", "Assam", "Himachal Pradesh", "Uttarakhand",
    "Goa", "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry",
    "Tam Nad", "TN", "Tamilnadu"
]

TN_DISTRICTS = [
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    "Tirunelveli", "Vellore", "Erode", "Thoothukudi", "Dindigul",
    "Thanjavur", "Ranipet", "Sivaganga", "Virudhunagar", "Nagapattinam",
    "Kanyakumari", "Krishnagiri", "Dharmapuri", "Namakkal", "Cuddalore",
    "Villupuram", "Tiruvannamalai", "Perambalur", "Ariyalur", "Karur",
    "Tirupur", "Nilgiris", "Pudukkottai", "Ramanathapuram", "Sivagangai",
    "Tenkasi", "Chengalpattu", "Kallakurichi", "Mayiladuthurai"
]

TN_TALUKS = [
    "Tirunelveli", "Palayamkottai", "Ambasamudram", "Nanguneri",
    "Radhapuram", "Cheranmahadevi", "Sankarankovil", "Tenkasi",
    "Kadayanallur", "Sivakasi", "Virudhunagar", "Srivilliputhur",
    "Madurai", "Dindigul", "Salem", "Erode", "Coimbatore",
    "Alangulam", "Veeravanallur", "sivagiri",
    "Shencottai", "Courtallam"
]

def fuzzy_find_in_list(text, word_list):
    text_upper = text.upper()
    for item in word_list:
        if item.upper() in text_upper:
            return item
    for item in word_list:
        if len(item) >= 5:
            for i in range(0, len(item)-3):
                chunk = item[i:i+5].upper()
                if chunk in text_upper:
                    return item
    return ""

# ─────────────────────────────────────────────
# AADHAAR EXTRACTION
# ─────────────────────────────────────────────
def extract_aadhaar(text):
    full_text = text
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    aadhaar_matches = re.findall(r"\b\d{4}\s?\d{4}\s?\d{4}\b", full_text)
    aadhaar_number = aadhaar_matches[0] if aadhaar_matches else ""

    dob_match = re.search(r"(?:DOB|Date of Birth|D\.O\.B|DO9|DO8|D09)[:\s/]*(\d{2}[/\-]\d{2}[/\-]\d{4})", full_text, re.IGNORECASE)
    if not dob_match:
        dob_match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", full_text)
    dob = dob_match.group(1) if dob_match else ""

    gender = ""
    txt_up = full_text.upper()
    if re.search(r"\bFEMALE\b", txt_up):
        gender = "Female"
    elif re.search(r"\bMALE\b", txt_up) or re.search(r"\br/Male\b", full_text, re.IGNORECASE):
        gender = "Male"

    phone = ""
    phone_candidates = re.findall(r"\b(\d{10})\b", full_text)
    for p in phone_candidates:
        if not re.search(p[:4] + r"\s?" + p[4:8] + r"\s?" + p[8:], aadhaar_number.replace(" ", "")):
            phone = p
            break

    pin_match = re.search(r"\b(\d{6})\b", full_text)
    pincode = pin_match.group(1) if pin_match else ""

    name = ""
    skip_kw = ["UNIQUE", "IDENTIFICATION", "AUTHORITY", "INDIA", "UIDAI", "AADHAAR",
                "ENROLLMENT", "GOVERNMENT", "YOUR", "DOWNLOAD", "STREET", "COLONY",
                "NAGAR", "ROAD", "VILLAGE", "POST", "DISTRICT", "TALUK", "STATE",
                "MALE", "FEMALE", "DOB", "PIN", "MOBILE"]
    to_match = re.search(r"\bTo\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)", full_text)
    if to_match:
        name = to_match.group(1).strip()
    else:
        for line in lines:
            line_up = line.upper()
            if len(line) > 2 and not any(kw in line_up for kw in skip_kw):
                if not re.search(r"\d", line):
                    if re.match(r"[A-Za-z\s]+$", line):
                        name = line.strip()
                        break

    guardian = ""
    guardian_match = re.search(r"(?:S/O|D/O|W/O|C/O)[:\s]*([A-Za-z\s:]+?)(?:\s{2,}|\d|/)", full_text, re.IGNORECASE)
    if guardian_match:
        guardian = guardian_match.group(1).strip().rstrip(":")

    street_match = re.search(
        r"(\d+[/\-]?\w*\s+(?:STREET|ST|ROAD|RD|NAGAR|COLONY|LAYOUT|SALAI)[^\d\n]{0,60})",
        full_text, re.IGNORECASE
    )
    street = street_match.group(1).strip() if street_match else ""

    taluk = fuzzy_find_in_list(full_text, TN_TALUKS)
    district = fuzzy_find_in_list(full_text, TN_DISTRICTS)
    state_raw = fuzzy_find_in_list(full_text, INDIA_STATES)
    state_map = {"Tam Nad": "Tamil Nadu", "TN": "Tamil Nadu", "Tamilnadu": "Tamil Nadu"}
    state = state_map.get(state_raw, state_raw)

    address = ""
    if street and pincode:
        addr_match = re.search(
            re.escape(street[:15]) + r"(.+?)" + re.escape(pincode),
            full_text, re.IGNORECASE | re.DOTALL
        )
        if addr_match:
            address = (street + addr_match.group(1)).strip()
    elif street:
        address = street

    return {
        "document_type": "Aadhaar Card",
        "name": name,
        "father_guardian": guardian,
        "dob": dob,
        "gender": gender,
        "aadhaar_number": aadhaar_number,
        "phone": phone,
        "street": street,
        "address": address,
        "taluk": taluk,
        "district": district,
        "state": state if state else "Tamil Nadu",
        "pincode": pincode,
    }

# ─────────────────────────────────────────────
# RESUME EXTRACTION
# ─────────────────────────────────────────────
def extract_resume(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    name = lines[0] if lines else ""

    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    email = email_match.group() if email_match else ""

    phone_match = re.search(r"(\+?91[-\s]?\d{10}|\b\d{10}\b)", text)
    phone = phone_match.group() if phone_match else ""

    CITIES = [
        "Tirunelveli", "Chennai", "Coimbatore", "Madurai", "Salem", "Erode",
        "Trichy", "Tiruchirappalli", "Thoothukudi", "Tuticorin", "Vellore",
        "Dindigul", "Thanjavur", "Nagercoil", "Kanyakumari", "Tenkasi",
        "Bangalore", "Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Pune",
        "Kolkata", "Ahmedabad", "Jaipur", "Lucknow", "Bhopal", "Indore",
        "Kochi", "Thiruvananthapuram", "Visakhapatnam", "Vijayawada"
    ]
    location = ""
    for city in CITIES:
        if re.search(r"\b" + re.escape(city) + r"\b", text, re.IGNORECASE):
            location = city
            break

    github_match = re.search(r"github\.com/[A-Za-z0-9._/-]+", text, re.IGNORECASE)
    github = "https://" + github_match.group() if github_match else ""

    linkedin_match = re.search(r"linkedin\.com/in/[A-Za-z0-9._/-]+", text, re.IGNORECASE)
    linkedin = "https://" + linkedin_match.group() if linkedin_match else ""

    skills = []
    skills_match = re.search(r"(?:SKILLS?|TECHNICAL SKILLS?)[:\s\n]+(.*?)(?:\n[A-Z]{3,}|\Z)", text, re.IGNORECASE | re.DOTALL)
    if skills_match:
        skills_raw = skills_match.group(1)
        skills = [s.strip() for s in re.split(r"[,|\n•\-●]", skills_raw) if s.strip() and len(s.strip()) > 1]
        skills = skills[:15]

    summary = ""
    summary_match = re.search(r"(?:SUMMARY|OBJECTIVE|PROFILE|ABOUT)[:\s\n]+(.*?)(?:\n[A-Z]{3,}|\Z)", text, re.IGNORECASE | re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()[:500]

    education = ""
    edu_match = re.search(r"(?:EDUCATION|QUALIFICATION)[:\s\n]+(.*?)(?:\n[A-Z]{3,}|\Z)", text, re.IGNORECASE | re.DOTALL)
    if edu_match:
        education = edu_match.group(1).strip()[:300]

    experience = ""
    exp_match = re.search(r"(?:EXPERIENCE|WORK EXPERIENCE|INTERNSHIP)[:\s\n]+(.*?)(?:\n[A-Z]{3,}|\Z)", text, re.IGNORECASE | re.DOTALL)
    if exp_match:
        experience = exp_match.group(1).strip()[:300]

    certs = []
    cert_match = re.search(r"(?:CERTIFICATION|CERTIFICATES?)[:\s\n]+(.*?)(?:\n[A-Z]{3,}|\Z)", text, re.IGNORECASE | re.DOTALL)
    if cert_match:
        certs_raw = cert_match.group(1)
        certs = [c.strip() for c in re.split(r"[,\n•\-●]", certs_raw) if c.strip() and len(c.strip()) > 2]
        certs = certs[:10]

    return {
        "document_type": "Resume / CV",
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "github": github,
        "linkedin": linkedin,
        "summary": summary,
        "skills": skills,
        "education": education,
        "experience": experience,
        "certifications": certs
    }

# ─────────────────────────────────────────────
# OFFER LETTER EXTRACTION
# ─────────────────────────────────────────────
def extract_offer_letter(text):
    name_match = re.search(r"(?:Dear|To)[:\s]+([A-Za-z][A-Za-z\s]{2,40})(?:,|\n)", text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else ""

    company_match = re.search(r"(?:Company|Organization|From)[:\s]+([^\n]+)", text, re.IGNORECASE)
    if not company_match:
        company_match = re.search(r"(?:Opportunity at|at)\s+([A-Z][A-Za-z0-9\s\(\)]+?)(?:\n|,|\.|$)", text)
    if not company_match:
        company_match = re.search(r"^([A-Z][A-Z\s\(\)]{5,60}(?:LIMITED|LTD|PVT|PRIVATE|SERVICES|TECHNOLOGIES|SOLUTIONS|SYSTEMS)[\w\s\(\)]*)", text, re.MULTILINE)
    company = company_match.group(1).strip() if company_match else ""

    role_match = re.search(r"(?:position of|role of|designation of|as a|as an|Role|Position|Designation)[:\s\-]+([^\n]{3,80})", text, re.IGNORECASE)
    role = role_match.group(1).strip() if role_match else ""

    date_match = re.search(r"(?:Date|Joining Date|Start Date|Commencement)[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})", text, re.IGNORECASE)
    if not date_match:
        date_match = re.search(r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\b", text)
    date = date_match.group(1) if date_match else ""

    stipend_match = re.search(r"(?:Stipend|Salary|CTC|Remuneration|Compensation)[:\s]*([^\n]{2,40})", text, re.IGNORECASE)
    stipend = stipend_match.group(1).strip() if stipend_match else ""

    duration_match = re.search(r"(?:Duration|Period|for a period of)[:\s]*([^\n]{2,40})", text, re.IGNORECASE)
    duration = duration_match.group(1).strip() if duration_match else ""

    return {
        "document_type": "Offer Letter",
        "candidate_name": name,
        "company": company,
        "role": role,
        "date": date,
        "stipend": stipend,
        "duration": duration
    }

# ─────────────────────────────────────────────
# BIRTH CERTIFICATE EXTRACTION
# ─────────────────────────────────────────────
def extract_birth_certificate(text):
    name_match = re.search(r'(?:Name of Child|Child Name|Name)[:\s]+([A-Za-z\s]+?)(?:\\n|,)', text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else ""

    dob_match = re.search(r'(?:Date of Birth|Born on|DOB)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text, re.IGNORECASE)
    dob = dob_match.group(1) if dob_match else ""

    gender = ""
    if re.search(r"\bFEMALE\b|\bGIRL\b", text.upper()):
        gender = "Female"
    elif re.search(r"\bMALE\b|\bBOY\b", text.upper()):
        gender = "Male"

    father_match = re.search(r"(?:Father[\''s]*\s*Name|Father)[:\s]+([A-Za-z\s]+?)(?:\n|,)", text, re.IGNORECASE)
    father = father_match.group(1).strip() if father_match else ""

    mother_match = re.search(r"(?:Mother[\''s]*\s*Name|Mother)[:\s]+([A-Za-z\s]+?)(?:\n|,)", text, re.IGNORECASE)
    mother = mother_match.group(1).strip() if mother_match else ""

    place_match = re.search(r"(?:Place of Birth|Born at)[:\s]+([^\n]+)", text, re.IGNORECASE)
    place = place_match.group(1).strip() if place_match else ""

    reg_match = re.search(r"(?:Registration No|Reg No|Cert No)[:\s]*([\w/-]+)", text, re.IGNORECASE)
    reg_no = reg_match.group(1).strip() if reg_match else ""

    return {
        "document_type": "Birth Certificate",
        "name": name,
        "dob": dob,
        "gender": gender,
        "father_name": father,
        "mother_name": mother,
        "place_of_birth": place,
        "registration_no": reg_no
    }

# ─────────────────────────────────────────────
# BONAFIDE CERTIFICATE EXTRACTION
# ─────────────────────────────────────────────
def extract_bonafide(text):
    name_match = re.search(r"(?:Mr\.|Ms\.|Miss\.|Sri\.|Thiru\.)?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\s+(?:is a|was a|is student|has been)", text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else ""

    rollno_match = re.search(r"(?:Roll No|Register No|Reg No|Enrollment No)[:\s]*([\w/-]+)", text, re.IGNORECASE)
    rollno = rollno_match.group(1).strip() if rollno_match else ""

    course_match = re.search(r"(?:studying in|enrolled in|course|department|programme)[:\s]*([^\n]+)", text, re.IGNORECASE)
    course = course_match.group(1).strip() if course_match else ""

    year_match = re.search(r"(?:year|semester|batch)[:\s]*([^\n]+)", text, re.IGNORECASE)
    year = year_match.group(1).strip() if year_match else ""

    institution_match = re.search(r"(?:college|university|school|institution)[:\s]*([^\n]+)", text, re.IGNORECASE)
    institution = institution_match.group(1).strip() if institution_match else ""

    return {
        "document_type": "Bonafide Certificate",
        "name": name,
        "roll_no": rollno,
        "course": course,
        "year": year,
        "institution": institution
    }

# ─────────────────────────────────────────────
# TRANSFER CERTIFICATE EXTRACTION
# ─────────────────────────────────────────────
def extract_transfer_certificate(text):
    name_match = re.search(r"(?:Name of Student|Name of Pupil|Name)[:\s]+([A-Za-z\s]+?)(?:\n|,)", text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else ""

    dob_match = re.search(r"(?:Date of Birth|DOB)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text, re.IGNORECASE)
    dob = dob_match.group(1) if dob_match else ""

    tcno_match = re.search(r"(?:TC No|T\.C\. No|Transfer Certificate No)[:\s]*([\w/-]+)", text, re.IGNORECASE)
    tcno = tcno_match.group(1).strip() if tcno_match else ""

    school_match = re.search(r"(?:School|Institution|College)[:\s]*([^\n]+)", text, re.IGNORECASE)
    school = school_match.group(1).strip() if school_match else ""

    conduct_match = re.search(r"(?:Conduct|Character)[:\s]*([^\n]+)", text, re.IGNORECASE)
    conduct = conduct_match.group(1).strip() if conduct_match else ""

    return {
        "document_type": "Transfer Certificate",
        "name": name,
        "dob": dob,
        "tc_no": tcno,
        "school": school,
        "conduct": conduct
    }

# ─────────────────────────────────────────────
# MARKSHEET EXTRACTION
# ─────────────────────────────────────────────
def extract_marksheet(text):
    name_match = re.search(r"(?:Name of Student|Student Name|Name)[:\s]+([A-Za-z\s]+?)(?:\n|,|Register)", text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else ""

    rollno_match = re.search(r"(?:Roll No|Register No|Reg No|Enrollment)[:\s]*([\w/-]+)", text, re.IGNORECASE)
    rollno = rollno_match.group(1).strip() if rollno_match else ""

    cgpa_match = re.search(r"(?:CGPA|GPA)[:\s]*([\d.]+)", text, re.IGNORECASE)
    cgpa = cgpa_match.group(1) if cgpa_match else ""

    percentage_match = re.search(r"(?:Percentage|Total %|Marks %)[:\s]*([\d.]+)", text, re.IGNORECASE)
    percentage = percentage_match.group(1) if percentage_match else ""

    semester_match = re.search(r"(?:Semester|Sem)[:\s]*([^\n]+)", text, re.IGNORECASE)
    semester = semester_match.group(1).strip() if semester_match else ""

    result_match = re.search(r"(?:Result|Status)[:\s]*(PASS|FAIL|PASSED|FAILED)", text, re.IGNORECASE)
    result = result_match.group(1).upper() if result_match else ""

    course_match = re.search(r"(?:Course|Programme|Department)[:\s]*([^\n]+)", text, re.IGNORECASE)
    course = course_match.group(1).strip() if course_match else ""

    return {
        "document_type": "Marksheet / Result",
        "name": name,
        "roll_no": rollno,
        "course": course,
        "semester": semester,
        "cgpa": cgpa,
        "percentage": percentage,
        "result": result
    }

# ─────────────────────────────────────────────
# INTERNSHIP CERTIFICATE EXTRACTION
# ─────────────────────────────────────────────
def extract_internship_certificate(text):
    name_match = re.search(r"(?:Mr\.|Ms\.|Miss\.)?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\s+(?:has successfully|has completed|worked as|interned)", text, re.IGNORECASE)
    if not name_match:
        name_match = re.search(r"(?:Dear|To|Name)[:\s]+([A-Za-z\s]+?)(?:,|\n)", text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else ""

    company_match = re.search(r"(?:Company|Organization|Firm|at)[:\s]+([^\n]+)", text, re.IGNORECASE)
    company = company_match.group(1).strip() if company_match else ""

    role_match = re.search(r"(?:Role|Position|Designation|as a|as an)[:\s]+([^\n]+)", text, re.IGNORECASE)
    role = role_match.group(1).strip() if role_match else ""

    duration_match = re.search(r"(?:Duration|Period|From)[:\s]*([^\n]+)", text, re.IGNORECASE)
    duration = duration_match.group(1).strip() if duration_match else ""

    return {
        "document_type": "Internship Certificate",
        "name": name,
        "company": company,
        "role": role,
        "duration": duration
    }

# ─────────────────────────────────────────────
# MAIN UI
# ─────────────────────────────────────────────
st.title("📄 AI Document Analyzer")

uploaded = st.file_uploader("Upload File", type=["pdf", "png", "jpg", "jpeg"])

if uploaded:
    if uploaded.name.lower().endswith(".pdf"):
        text = extract_pdf(uploaded)
    else:
        image = Image.open(uploaded)
        text = extract_image(image)

    st.subheader("Extracted Text")
    st.text_area("", text, height=250)

    doc_type = classify_document(text)
    st.info(f"Document Type Detected: **{doc_type}**")

    if doc_type == "AADHAAR":
        parsed = extract_aadhaar(text)
    elif doc_type == "RESUME":
        parsed = extract_resume(text)
    elif doc_type == "OFFER_LETTER":
        parsed = extract_offer_letter(text)
    elif doc_type == "BIRTH_CERTIFICATE":
        parsed = extract_birth_certificate(text)
    elif doc_type == "BONAFIDE":
        parsed = extract_bonafide(text)
    elif doc_type == "TRANSFER_CERTIFICATE":
        parsed = extract_transfer_certificate(text)
    elif doc_type == "MARKSHEET":
        parsed = extract_marksheet(text)
    elif doc_type == "INTERNSHIP_CERTIFICATE":
        parsed = extract_internship_certificate(text)
    else:
        parsed = {"note": "Unknown document type. Raw text extracted above."}

    st.subheader("Extracted Information")
    st.json(parsed)

    cur.execute("INSERT INTO documents(filename,content) VALUES (?,?)", (uploaded.name, text))
    conn.commit()

    st.download_button(
        "Download JSON",
        json.dumps(parsed, indent=4),
        file_name="output.json"
    )

st.sidebar.title("Stored Documents")
rows = cur.execute("SELECT filename FROM documents").fetchall()
for row in rows:
    st.sidebar.write(row[0])