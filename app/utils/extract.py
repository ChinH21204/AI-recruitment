import pdfplumber
import docx2txt
import os

def extract_text(file_path):
    text = ""
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    elif file_path.endswith(".docx"):
        text = docx2txt.process(file_path)
    return text

def extract_all_cvs(folder_path):
    cvs = {}
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        cvs[file] = extract_text(file_path)
    return cvs
