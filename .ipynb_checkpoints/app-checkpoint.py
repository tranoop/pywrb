from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import numpy as np
import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PROCESSED_FOLDER'] = 'processed/'

# Ensure the upload and processed directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file and file.filename.endswith('.SDT'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        process_SDT_file(filepath)
        return redirect(url_for('processed_files'))
    
    return redirect(request.url)

@app.route('/processed')
def processed_files():
    files = os.listdir(app.config['PROCESSED_FOLDER'])
    return render_template('processed.html', files=files)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

# Your existing functions go here...
# Include all the functions from your original script, such as `process_SDT_file`, `read_header`, etc.

if __name__ == '__main__':
    app.run(debug=True)