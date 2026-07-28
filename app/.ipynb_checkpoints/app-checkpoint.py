from flask import Flask, render_template, request
import pickle 
import string 
import os 
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# OCR libraries
import pytesseract
from PIL import Image
import pdfplumber
import docx

app = Flask(__name__)

# Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load saved model
with open("C:\\Users\\Lenovo\\Desktop\\Minor Project\\project - Copy\\LegalDocDetector\\model\\model.pkl", "rb") as f:
    model = pickle.load(f)

# Load saved vectorizer
with open("C:\\Users\\Lenovo\\Desktop\\Minor Project\\project - Copy\\LegalDocDetector\\model\\vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# Cleaning function
def clean_text(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text

# Function to extract text from files
def extract_text_from_file(file_path):

    if file_path.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text()
        return text

    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        text = " ".join([para.text for para in doc.paragraphs])
        return text

    elif file_path.endswith((".png", ".jpg", ".jpeg")):
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text

    else:
        return ""

@app.route("/", methods=["GET", "POST"])
def home():

    prediction_result = None
    text_to_check = ""
    if request.method == "POST":

        # OPTION 1 : TEXT INPUT
        user_text = request.form.get("document_text")

        # OPTION 2 : FILE INPUT
        uploaded_file = request.files.get("file")

        text_to_check = ""

        if uploaded_file and uploaded_file.filename != "":
            filepath = os.path.join("uploads", uploaded_file.filename)
            uploaded_file.save(filepath)

            text_to_check = extract_text_from_file(filepath)

        elif user_text and user_text.strip() != "":
            text_to_check = user_text

        else:
            prediction_result = "Please enter text or upload a file."
            return render_template("index.html", result=prediction_result)

        cleaned = clean_text(text_to_check)
        vectorized = vectorizer.transform([cleaned])
        prediction = model.predict(vectorized)

        if prediction[0] == 1:
            prediction_result = "Legal Document"
        else:
            prediction_result = "Non-Legal Document"

    return render_template("index.html", result=prediction_result, extracted_text=text_to_check)


if __name__ == "__main__":
    app.run(debug=True)