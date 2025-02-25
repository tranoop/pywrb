from flask import Flask, render_template, request, send_from_directory, send_file
import os
from process_SDT_file import process_SDT_file  # Ensure this is correctly imported
from SPT_to_NC import convert_spt_to_nc  # Import your function
import zipfile

# Flask app setup
app = Flask(__name__)

# Define folders for uploads and processed files
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
CONVERTED_FOLDER = "converted_nc_files"

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)


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
def process():
    """Process multiple uploaded SDT files."""
    files = os.listdir(UPLOAD_FOLDER)  # Get available files
    
    if request.method == 'POST':
        selected_files = request.form.getlist('files[]')  # Retrieve selected files
        print(f"Selected files: {selected_files}")  # Debugging output

        if not selected_files:
            return "<p style='color: red;'>No files selected for processing.</p>", 400

        # Clear old processed files before adding new ones
        for old_file in os.listdir(PROCESSED_FOLDER):
            os.remove(os.path.join(PROCESSED_FOLDER, old_file))
        
        for filename in selected_files:
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(filepath):
                process_SDT_file(filepath)  # Process file (Ensure this function saves output in PROCESSED_FOLDER)
                os.remove(filepath)  # Remove file after processing
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
    """Allow users to download processed files individually."""
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

@app.route('/download_all')
def download_all():
    """Create and serve a ZIP file containing all processed files."""
    processed_files = os.listdir(PROCESSED_FOLDER)
    
    # Debug: Print processed files
    print("Processed Files:", processed_files)
    
    if not processed_files:
        return "<p style='color: red;'>No processed files available to download.</p>", 400

    # Create a temporary ZIP file
    zip_path = os.path.join(PROCESSED_FOLDER, "processed_files.zip")
    
    # Debug: Print ZIP file path
    print("ZIP File Path:", zip_path)
    
    try:
        # Create ZIP file
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in processed_files:
                file_path = os.path.join(PROCESSED_FOLDER, file)
                zipf.write(file_path, file)  # Add file to ZIP
                print(f"Added {file} to ZIP")
        
        # Debug: Confirm ZIP creation
        print("ZIP file created successfully")
        
        # Send the ZIP file to the user
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        # Debug: Print any errors
        print(f"Error creating ZIP file: {e}")
        return f"<p style='color: red;'>Error creating ZIP file: {e}</p>", 500

@app.route('/convert_spt', methods=['GET', 'POST'])
def convert_spt():
    if request.method == 'POST':
        uploaded_files = request.files.getlist('spt_files')
        if not uploaded_files:
            return render_template('convert_spt.html', message="No SPT files selected!")

        output_folder = "converted_nc_files"
        os.makedirs(output_folder, exist_ok=True)

        temp_input_folder = "temp_spt_files"
        os.makedirs(temp_input_folder, exist_ok=True)

        saved_files = []
        for file in uploaded_files:
            file_path = os.path.join(temp_input_folder, file.filename)
            file.save(file_path)
            saved_files.append(file_path)

        try:
            convert_spt_to_nc(temp_input_folder, output_folder)
            return render_template('convert_spt.html', message=f"Conversion completed! NetCDF files saved in {output_folder}")
        except Exception as e:
            return render_template('convert_spt.html', message=f"Error during conversion: {e}")

    return render_template('convert_spt.html')
@app.route('/delete_all', methods=['POST'])
def delete_all():
    """Delete all files in uploads, processed, and converted folders."""
    try:
        for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, CONVERTED_FOLDER]:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                os.remove(file_path)
        return jsonify({"message": "All files deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
