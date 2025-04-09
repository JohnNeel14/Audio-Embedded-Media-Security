from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import numpy as np
import wave
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'static/decrypt'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# AES encryption key and IV
AES_KEY = os.urandom(32)  # 32 bytes key (256-bit)
AES_IV = os.urandom(16)  # 16 bytes IV

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encrypt_image(image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
    
    # Pad image data to be a multiple of AES block size
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(image_data) + padder.finalize()
    
    # Encrypt the image data using AES-CBC
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    
    return encrypted_data

def encode_audio(encrypted_data):
    # Convert encrypted image data to audio format (dummy implementation)
    with wave.open('output.wav', 'wb') as audio_file:
        audio_file.setnchannels(1)  # Mono
        audio_file.setsampwidth(2)   # Sample width in bytes
        audio_file.setframerate(44100)  # Sample rate
        audio_file.writeframes(encrypted_data)  # Truncate to match the WAV file size

def decode_audio(audio_file):
    with wave.open(audio_file, 'rb') as audio:
        frames = audio.readframes(audio.getnframes())
    return frames

def decrypt_image(encrypted_data):
    # Decrypt the image data using AES-CBC
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
    
    # Unpad the decrypted data
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()
    
    return unpadded_data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Create the uploads directory if it doesn't exist
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            
            # Save the file in the uploads directory
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Encrypt the image and encode it into audio
            encrypted_data = encrypt_image(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            encode_audio(encrypted_data)
            return render_template('result.html', message="Image encrypted and audio file created.")
    return render_template('index.html')

@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        audio_file = request.files['file']
        if audio_file:
            # Decode the audio to get encrypted image data
            encrypted_data = decode_audio(audio_file)
            
            # Decrypt the image data
            decrypted_data = decrypt_image(encrypted_data)
            
            # Save the decrypted image to disk
            decrypted_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'decrypted_image.png')
            with open(decrypted_image_path, 'wb') as image_file:
                image_file.write(decrypted_data)
            return render_template('result.html', message="Image decrypted.", image="decrypt/decrypted_image.png")
    return render_template('index.html')
if __name__ == '__main__':
    app.run(debug=True)
