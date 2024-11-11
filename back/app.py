import json
import os
import requests
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import logging

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def save_uploaded_image(image):
    """Save the uploaded image and return the path to the saved file."""
    if image.filename == '':
        raise ValueError('No selected image')

    unique_filename = f"{os.path.splitext(image.filename)[0]}_{int(os.times()[4])}.png"
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    image.save(image_path)
    return image_path

def extract_text_from_image(image_path):
    """Extract text from an image using Tesseract OCR."""
    try:
        extracted_text = pytesseract.image_to_string(Image.open(image_path)).strip()
        return extracted_text
    except Exception as e:
        app.logger.error(f"Error during OCR processing: {e}")
        raise e

def extract_book_data_with_llama3(ocr_text):
    """Send OCR text to the local LLaMA 3 model and extract structured book data."""
    api_url = "http://localhost:11434/api/generate"  
    headers = {
        "Content-Type": "applicaiton/json"
    }

    prompt = f"""
    "Extract structured book information from the following text and format it as JSON with the keys: title, author, cover, genre, publisher, and year_published. 
    If any information is missing or unavailable from the provided text, please mark it as 'Not specified'.

    Text:
    {ocr_text}

    Output JSON:
    """
    data = {"model": "llama3", "prompt": prompt, "stream": False}
    print(f'DUMPS DATA {json.dumps(data)}' )
    print(data)
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        output_text = result.get("text", "").strip()
        book_data = json.loads(output_text)
        return book_data
    except requests.RequestException as e:
        app.logger.error(f"Error connecting to LLaMA API: {e}")
        return {"error": "Failed to connect to LLaMA API"}
    except json.JSONDecodeError as e:
        app.logger.error(f"Error decoding LLaMA response: {e}, Response text: {response.text}")
        print(f'Error decoding LLaMa response: {e}')

        return {"error": "Invalid response format from LLaMA API"}

def update_json_file(json_file_path, new_book_data):
    """Update the given JSON file with new book data."""
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                data = json.load(file)
        else:
            data = []

        data.append(new_book_data)

        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=4)
        app.logger.info(f"Updated {json_file_path} successfully.")
    except Exception as e:
        app.logger.error(f"Error updating JSON file: {e}")

@app.route('/upload-image', methods=['POST'])
def upload_image():
    """Handle image upload, OCR text extraction, and book data extraction."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400

        image = request.files['image']
        image_path = save_uploaded_image(image)

        # Extract text using OCR
        ocr_text = extract_text_from_image(image_path)
        if not ocr_text:
            return jsonify({'message': 'No text detected in the image', 'text': ''})

        # Extract book data using LLaMA model
        book_data = extract_book_data_with_llama3(ocr_text)

        # Save structured data if extraction was successful
        if "error" not in book_data:
            json_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'books.json')
            update_json_file(json_file_path, book_data)

        return jsonify({'message': 'Text extracted and processed successfully', 'data': book_data})
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        app.logger.error(f"Error processing image: {e}")
        return jsonify({'error': str(e)}), 500

# Testing
mytext=extract_text_from_image('/Users/gorodri/tavaresrodrigo/libreo/back/uploads/book1.jpg')
print(f"OCR text: {mytext}" )
print(extract_book_data_with_llama3(mytext))

if __name__ == '__main__':
    app.run(debug=True)
