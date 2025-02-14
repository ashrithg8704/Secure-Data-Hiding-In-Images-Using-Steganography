from flask import Flask, request, jsonify, send_file, render_template
import cv2
import numpy as np
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

def to_binary(data):
    """Convert data to binary format as string"""
    if isinstance(data, str):
        return ''.join([format(ord(i), '08b') for i in data])
    elif isinstance(data, bytes):
        return ''.join([format(i, '08b') for i in data])
    elif isinstance(data, np.ndarray):
        return [format(i, '08b') for i in data]
    elif isinstance(data, int) or isinstance(data, np.uint8):
        return format(data, '08b')
    else:
        raise TypeError("Type not supported.")

def encode_image(image_path, secret_data, password):
    """Encode data into image"""
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Could not read the image file")

    # Add password and terminator to secret data
    secret_data = password + "|||" + secret_data + "###"
    
    # Check if the image can hold the data
    n_bytes = image.shape[0] * image.shape[1] * 3 // 8
    if len(secret_data) > n_bytes:
        raise ValueError("Error: Insufficient bytes, need bigger image or less data!")

    binary_secret_data = to_binary(secret_data)
    data_len = len(binary_secret_data)
    
    data_index = 0
    for row in image:
        for pixel in row:
            if data_index < data_len:
                # Convert RGB values to binary
                r = to_binary(pixel[0])
                g = to_binary(pixel[1])
                b = to_binary(pixel[2])
                
                # Modify the least significant bit only if there is still data to store
                if data_index < data_len:
                    pixel[0] = int(r[:-1] + binary_secret_data[data_index], 2)
                    data_index += 1
                if data_index < data_len:
                    pixel[1] = int(g[:-1] + binary_secret_data[data_index], 2)
                    data_index += 1
                if data_index < data_len:
                    pixel[2] = int(b[:-1] + binary_secret_data[data_index], 2)
                    data_index += 1
                
                if data_index >= data_len:
                    break
        if data_index >= data_len:
            break
    
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'encryptedImage.png')
    cv2.imwrite(output_path, image)
    return output_path

def decode_image(image_path, password):
    """Decode the data from the image"""
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Could not read the image file")
    
    binary_data = ""
    for row in image:
        for pixel in row:
            binary_data += to_binary(pixel[0])[-1]
            binary_data += to_binary(pixel[1])[-1]
            binary_data += to_binary(pixel[2])[-1]

    # Convert binary to string
    all_bytes = [binary_data[i: i+8] for i in range(0, len(binary_data), 8)]
    decoded_data = ""
    for byte in all_bytes:
        decoded_data += chr(int(byte, 2))
        if decoded_data[-3:] == "###":  # Check for terminator
            break

    if "|||" not in decoded_data:
        raise ValueError("No valid data found in image")

    # Split password and message
    stored_password, message = decoded_data.split("|||")
    if stored_password != password:
        raise ValueError("Invalid password")

    return message[:-3]  # Remove terminator

@app.route('/encrypt', methods=['POST'])
def encrypt():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
            
        image = request.files['image']
        message = request.form.get('message')
        password = request.form.get('password')
        
        if not message or not password:
            return jsonify({'error': 'Message and password are required'}), 400
            
        # Save uploaded image
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        
        # Encrypt the message
        output_path = encode_image(image_path, message, password)
        
        # Send encrypted image file
        return send_file(output_path, mimetype='image/png', as_attachment=True, 
                        download_name='encryptedImage.png')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up uploaded file
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)

@app.route('/decrypt', methods=['POST'])
def decrypt():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
            
        image = request.files['image']
        password = request.form.get('password')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
            
        # Save uploaded image
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        
        # Decrypt the message
        message = decode_image(image_path, password)
        
        return jsonify({'message': message})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up uploaded file
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)

if __name__ == '__main__':
    app.run(debug=True)