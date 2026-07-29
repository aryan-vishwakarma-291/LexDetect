from flask import Flask, render_template, request
import pickle
import string
import os
import pytesseract
from PIL import Image
import pdfplumber
import docx

# Create Flask app FIRST
app = Flask(__name__) 

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load model
with open("model/model.pkl", "rb") as f:
    model = pickle.load(f)

# Load vectorizer
with open("model/vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# Cleaning function
def clean_text(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text


# Function to extract text from uploaded files
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
        return " ".join([para.text for para in doc.paragraphs])

    elif file_path.endswith((".png", ".jpg", ".jpeg")):
        image = Image.open(file_path)
        return pytesseract.image_to_string(image)

    else:
        return ""

@app.route("/", methods=["GET", "POST"])
def home():

    prediction_result = None
    text_to_check = ""
    confidence = None

    if request.method == "POST":

        # OPTION 1 : TEXT INPUT
        user_text = request.form.get("document_text")

        # OPTION 2 : FILE INPUT
        uploaded_file = request.files.get("file")

        if uploaded_file and uploaded_file.filename != "":
            os.makedirs("uploads", exist_ok=True)  # Create uploads folder if needed
            filepath = os.path.join("uploads", uploaded_file.filename)
            uploaded_file.save(filepath)

            text_to_check = extract_text_from_file(filepath)

        elif user_text and user_text.strip() != "":
            text_to_check = user_text

        else:
            prediction_result = "Please enter text or upload a file."
            return render_template("index.html", result=prediction_result)

        # Clean text
        cleaned = clean_text(text_to_check)

        # Convert text to vector
        vectorized = vectorizer.transform([cleaned])

        # Prediction
        prediction = model.predict(vectorized)

        # Confidence Score
        probability = model.predict_proba(vectorized)
        confidence = round(max(probability[0]) * 100, 2)

        # Result
        if prediction[0] == 1:
            prediction_result = "Legal Document"
        else:
            prediction_result = "Non-Legal Document"
            
    confidence = float(confidence)
    return render_template(
        "index.html",
        result=prediction_result,
        extracted_text=text_to_check,
        confidence=confidence
    )

if __name__ == "__main__":
    app.run(debug=True)