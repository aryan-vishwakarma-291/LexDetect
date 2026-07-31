from flask import Flask, render_template, request
import pickle
import string
import os
import pytesseract
from PIL import Image
import pdfplumber
import docx
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os
from flask import send_file
from database import init_db, save_prediction, get_history

# Create Flask app FIRST
app = Flask(__name__) 
init_db()  # Initialize the database
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load model
with open("model/model.pkl", "rb") as f:
    model = pickle.load(f)

# Load vectorizer
with open("model/vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# generate PDF
def generate_report(filename, prediction, confidence, text):

    os.makedirs("reports", exist_ok=True)

    pdf_path = os.path.join("reports", "prediction_report.pdf")

    doc = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("<b>AI Legal Document Detector</b>", styles["Title"]))

    story.append(Paragraph(f"<b>Prediction:</b> {prediction}", styles["Normal"]))

    story.append(Paragraph(f"<b>Confidence:</b> {confidence:.2f}%", styles["Normal"]))

    story.append(Paragraph(f"<b>File:</b> {filename}", styles["Normal"]))

    story.append(Paragraph(
        f"<b>Date:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
        styles["Normal"]
    ))

    story.append(Paragraph("<br/><b>Extracted Text:</b>", styles["Heading2"]))

    story.append(Paragraph(text[:3000], styles["BodyText"]))

    doc.build(story)

    return pdf_path
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

@app.route("/download-report")
def download_report():
    return send_file(
        "reports/prediction_report.pdf",
        as_attachment=True
    )

@app.route("/history")
def history():

    history_data = get_history()

    return render_template(
        "history.html",
        history=history_data
    )

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
        
        if uploaded_file:
            uploaded_filename = uploaded_file.filename
        else:
            uploaded_filename = user_text[:30] + "..." if len(user_text) > 30 else user_text
        report_path = generate_report(
        uploaded_filename,
        prediction_result,
        confidence,
        text_to_check
        )
        save_prediction(uploaded_filename, prediction_result, confidence)
    confidence = confidence

    return render_template(
        "index.html",
        result=prediction_result,
        extracted_text=text_to_check,
        confidence=confidence
    )

if __name__ == "__main__":
    app.run(debug=True)