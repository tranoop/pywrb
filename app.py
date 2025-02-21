from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import os
from process_SDT_file import process_SDT_file  # Ensure this is correctly imported

# Flask app setup
app = Flask(__name__)

# Define folders for uploads and processed files
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def home():
    """Home page with menu options."""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Handle SDT file uploads."""
    if request.method == 'POST':
        file = request.files.get('file')

        if not file or file.filename == '':
            return "<p style='color: red;'>No file selected!</p>", 400
        
        if not file.filename.endswith('.SDT'):
            return "<p style='color: red;'>Invalid file type. Only .SDT files allowed.</p>", 400
        
        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        return "<p>File uploaded successfully!</p>"

    return render_template('upload.html')

@app.route('/process', methods=['GET', 'POST'])
def process():
    """Process an uploaded SDT file."""
    files = os.listdir(UPLOAD_FOLDER)

    if request.method == 'POST':
        filename = request.form.get('file')

        if not filename:
            return "<p style='color: red;'>No file selected for processing.</p>", 400

        filepath = os.path.join(UPLOAD_FOLDER, filename)

        if not os.path.exists(filepath):
            return "<p style='color: red;'>File not found!</p>", 400

        # Call the function from process_SDT_file.py
        process_SDT_file(filepath)

        return "<p>File processed successfully!</p>"

    return render_template('process.html', files=files)

@app.route('/save_output')
def save_output():
    """Show processed files available for download."""
    processed_files = os.listdir(PROCESSED_FOLDER)
    return render_template('save_output.html', processed_files=processed_files)

@app.route('/download/<filename>')
def download(filename):
    """Allow users to download processed files."""
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
