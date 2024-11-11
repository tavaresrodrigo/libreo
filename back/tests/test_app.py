import os
import io
from PIL import Image
import pytest
from app import app, UPLOAD_FOLDER

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = 'test_uploads'  # Temporary test folder
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def cleanup_test_uploads():
    """Ensure test uploads directory is clean before/after tests."""
    if not os.path.exists('test_uploads'):
        os.makedirs('test_uploads')
    yield
    for filename in os.listdir('test_uploads'):
        file_path = os.path.join('test_uploads', filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)

def test_upload_image_no_file(client):
    """Test uploading without a file."""
    response = client.post('/upload-image')
    assert response.status_code == 400
    assert 'No image uploaded' in response.get_json()['error']

def test_upload_image_with_file(client):
    """Test uploading an image and extracting text."""
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = (73, 109, 137))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    data = {
        'image': (img_bytes, 'test_image.png')
    }
    response = client.post('/upload-image', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert 'Text extracted successfully' in response.get_json()['message']
    # Check if the text file is created and contains the expected content
    extracted_text_path = os.path.join('test_uploads', 'extracted_text.txt')
    assert os.path.exists(extracted_text_path)

def test_extracted_text_empty(client):
    """Test extracting text from an image with no text."""
    # Create a blank image
    blank_img = Image.new('RGB', (100, 100), color = (255, 255, 255))
    img_bytes = io.BytesIO()
    blank_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    data = {
        'image': (img_bytes, 'blank_image.png')
    }
    response = client.post('/upload-image', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert 'No text detected in the image' in response.get_json().get('error', '')
