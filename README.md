# 📄 Document Ingestion Agent

A simple **Flask app** that ingests documents (PDFs, scanned images, etc.), extracts text and key fields using [Unstructured](https://github.com/Unstructured-IO/unstructured) and [OpenAI GPT](https://platform.openai.com/), and outputs structured data in **JSON or CSV** format.  

---

## 🚀 Features
- Upload PDF or scanned documents.  
- Extract structured text using `unstructured`.  
- Ask user which fields they want (e.g., landlord, tenant, rent).  
- If no fields are specified → auto-pick top 6–7 important ones.  
- Outputs results in a clean **table** with options to download as JSON or CSV.  

---

## 🛠️ Run Locally

### 1. Clone the Repo
```bash
git clone https://github.com/<your-username>/document-agent.git
cd document-agent
```

### Create virtual env
```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### Install dependencies
```bash
pip3 install -r requirements.txt
```

### Create .env file
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```
### Run the app
```bash
python app.py
```

### App will start on 
http://127.0.0.1:5000

### Requirements

Python 3.9+
Tesseract OCR
Poppler (for PDF → image conversion)
