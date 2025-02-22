from flask import Flask, render_template, request, send_from_directory
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
    """Handle multiple SDT file uploads."""
    if request.method == 'POST':
        files = request.files.getlist('files')

        if not files or all(file.filename == '' for file in files):
            return "<p style='color: red;'>No files selected!</p>", 400

        uploaded_files = []
        for file in files:
            if file and file.filename.endswith('.SDT'):
                filepath = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(filepath)
                uploaded_files.append(file.filename)

        return "<p>Files uploaded successfully: " + ", ".join(uploaded_files) + "</p>"

    return render_template('upload.html')

@app.route('/process', methods=['GET', 'POST'])
@app.route('/process', methods=['GET', 'POST'])
def process():
    """Process multiple uploaded SDT files."""
    files = os.listdir(UPLOAD_FOLDER)  # Get available files
    
    if request.method == 'POST':
        selected_files = request.form.getlist('files[]')  # Retrieve selected files
        print(f"Selected files: {selected_files}")  # Debugging output

        if not selected_files:
            return "<p style='color: red;'>No files selected for processing.</p>", 400

        for filename in selected_files:
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(filepath):
                process_SDT_file(filepath)
                os.remove(filepath)
            else:
                return f"<p style='color: red;'>File {filename} not found!</p>", 400

        return "<p>Files processed successfully!</p>"

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

