from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import os
import logging

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def process_image_with_ocr(image_path):
    """Process the image using Tesseract OCR and return the extracted text."""
    try:
        # Perform OCR on the image
        print("Extracting text")
        print(pytesseract.get_languages(config=''))
        extracted_text = pytesseract.image_to_string(Image.open(image_path))
        print (f'extracted_text: {extracted_text}')
        return extracted_text
    except Exception as e:
        app.logger.error(f"Error during OCR processing: {e}")
        raise e
    
process_image_with_ocr("/Users/tavaresrodrigo/libreo/back/uploads/book1.jpg")

@app.route('/upload-image', methods=['POST'])
def upload_image():
    """Handle the image upload, save it, and trigger OCR processing."""
    try:
        # Check if 'image' part is in the request
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400

        image = request.files['image']
        if image.filename == '':
            return jsonify({'error': 'No selected image'}), 400

        # Save the image with a unique filename
        unique_filename = f"{os.path.splitext(image.filename)[0]}_{int(os.times()[4])}.png"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        image.save(image_path)

        # Process the image using the separate OCR function
        extracted_text = process_image_with_ocr(image_path)

        # Handle case where no text is detected
        if not extracted_text:
            return jsonify({'message': 'No text detected in the image', 'text': ''})

        # Store the extracted text in a file
        text_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_text.txt')
        with open(text_file_path, 'a') as text_file:
            text_file.write(f"Text extracted from {unique_filename}:\n{extracted_text}\n\n")

        return jsonify({'message': 'Text extracted successfully', 'text': extracted_text})
    except Exception as e:
        app.logger.error(f"Error processing image: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
