# 📄 Smart Document Processing System

An AI-powered document analyzer built with **PaddleOCR**, **Streamlit**, and **Gmail OTP authentication**. Automatically detects and extracts key information from 8 types of Indian documents.

---

## 🚀 Features

- 🔐 **Secure Login** with email & password
- 📧 **Forgot Password** via Gmail OTP (2-minute expiry)
- 📄 **PDF & Image Upload** support (PNG, JPG, JPEG)
- 🤖 **Auto Document Detection** - 8 document types
- 📊 **Smart Field Extraction** using Regex + PaddleOCR
- 💾 **SQLite Database** storage for uploaded documents
- 📥 **JSON Download** of extracted data

---

## 🗂️ Supported Document Types

| Document | Extracted Fields |
|----------|-----------------|
| Aadhaar Card | Name, DOB, Gender, Address, Pincode, District, State |
| Resume / CV | Name, Email, Phone, Skills, Education, Experience, GitHub, LinkedIn |
| Offer Letter | Candidate Name, Company, Role, Stipend, Duration, Joining Date |
| Birth Certificate | Name, DOB, Gender, Father, Mother, Place of Birth |
| Bonafide Certificate | Name, Roll No, Course, Year, Institution |
| Transfer Certificate | Name, DOB, TC No, School, Conduct |
| Marksheet | Name, Roll No, CGPA, Percentage, Semester, Result |
| Internship Certificate | Name, Company, Role, Duration |

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **OCR:** PaddleOCR
- **PDF Parsing:** pdfplumber
- **Image Processing:** OpenCV, NumPy, Pillow
- **OTP:** pyotp + Gmail SMTP
- **Database:** SQLite3
- **Language:** Python 3.9

---

## ⚙️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/jegadheeshjega492-art/smart-document-processing-system.git
cd smart-document-processing-system

# 2. Create virtual environment
python -m venv ocr_env
ocr_env\Scripts\activate      # Windows
# source ocr_env/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run "smart document processing system.py"
```

---

## 🔧 Configuration

Open `smart document processing system.py` and update:

```python
USERNAME = "your_email@gmail.com"        # Login email
DEFAULT_PASSWORD = "YourPassword"         # Default login password
GMAIL_USER = "your_email@gmail.com"      # Gmail sender
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"  # Gmail App Password
```

### How to generate Gmail App Password:
1. Go to [myaccount.google.com](https://myaccount.google.com) → Security
2. Enable **2-Step Verification**
3. Search **"App Passwords"** → Create
4. Copy the 16-digit password and paste above

---

## 📸 Screenshots

### Login Page
![Login](screenshots/login.png)

### Document Upload & Extraction
![Extraction](screenshots/extraction.png)

---

## 📁 Project Structure

```
smart-document-processing-system/
│
├── smart document processing system.py   # Main application
├── requirements.txt                       # Dependencies
├── current_password.txt                   # Stores current password (auto-created)
├── otp_secret.txt                         # OTP secret key (auto-created)
├── documents.db                           # SQLite database (auto-created)
└── README.md                              # This file
```

---

## 👨‍💻 Author

**Jegadheesh**  
B.E. Electronics and Communication Engineering  
Government College of Engineering, Tirunelveli  

- GitHub: [@jegadheeshjega492-art](https://github.com/jegadheeshjega492-art)
- LinkedIn: [jegadheesh](https://linkedin.com/in/jegadheesh-jegadheesh-8b758b3ab)

---

## 📝 License

This project is for educational purposes.
