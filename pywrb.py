from flask import Flask, render_template, request, send_from_directory, send_file, url_for, session, jsonify
import os
import pandas as pd
import numpy as np
import glob
from process_SDT_file import process_SDT_file  # Ensure this is correctly imported
from SPT_to_NC import convert_spt_to_nc  # Import your function
from remove_spike import remove_spike
import zipfile
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
from windsea_swell_seperation import windsea_swell_seperation  # Import the wind-sea-swell separation function
from os import path


# Flask app setup
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for session handling

# Define folders for uploads and processed files
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
CONVERTED_FOLDER = "converted_nc_files"
TEMP_SPT_FOLDER = "temp_spt_files"
PLOT_FOLDER = "static/plots"  # ✅ This was missing before!

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)
os.makedirs(TEMP_SPT_FOLDER, exist_ok=True)
os.makedirs(PLOT_FOLDER, exist_ok=True)

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

        os.makedirs(CONVERTED_FOLDER, exist_ok=True)
        os.makedirs(TEMP_SPT_FOLDER, exist_ok=True)

        # Save uploaded files
        for file in uploaded_files:
            file_path = os.path.join(TEMP_SPT_FOLDER, file.filename)
            file.save(file_path)

        try:
            # Convert all files in TEMP_SPT_FOLDER
            convert_spt_to_nc(TEMP_SPT_FOLDER, CONVERTED_FOLDER)

            # Get converted files
            converted_files = os.listdir(CONVERTED_FOLDER)
            if converted_files:
                return render_template('convert_spt.html', message="Conversion completed! You can now download the files.")
            else:
                return render_template('convert_spt.html', message="No NetCDF files were created. Please check input data.")
        except Exception as e:
            return render_template('convert_spt.html', message=f"Error during conversion: {e}")

    return render_template('convert_spt.html')

@app.route('/download_nc_all')
def download_nc_all():
    """Create and serve a ZIP file containing all converted NetCDF files."""
    netcdf_files = os.listdir(CONVERTED_FOLDER)
    
    if not netcdf_files:
        return "<p style='color: red;'>No NetCDF files available to download.</p>", 400

    zip_path = os.path.join(CONVERTED_FOLDER, "converted_nc_files.zip")
    
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in netcdf_files:
                file_path = os.path.join(CONVERTED_FOLDER, file)
                zipf.write(file_path, file)
        
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        return f"<p style='color: red;'>Error creating ZIP file: {e}</p>", 500

@app.route('/delete_all', methods=['POST'])
def delete_all():
    """Delete all files in uploads, processed, and converted folders."""
    try:
        for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, CONVERTED_FOLDER, TEMP_SPT_FOLDER, PLOT_FOLDER]:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                os.remove(file_path)
        return jsonify({"message": "All files deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/remove_spike', methods=['GET', 'POST'])
def remove_spike_route():
    """Handle spike removal functionality with persistent file storage for trial and error."""
    file_path = session.get('uploaded_his_file')  # Retrieve stored file path
    processed_file_path = None  # File path for downloading the processed file

    if request.method == 'POST':
        uploaded_files = request.files.getlist('his_files')

        # If a new file is uploaded, store it
        if uploaded_files and uploaded_files[0].filename != '':
            file = uploaded_files[0]
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            session['uploaded_his_file'] = file_path  # Update session with new file

        if not file_path or not os.path.exists(file_path):
            return render_template('remove_spike.html', message="Error: No file uploaded!")

        try:
            # Get input values
            window = int(request.form.get('window', 2))
            threshold = float(request.form.get('threshold', 0.1))
            abnormal_max = float(request.form.get('abnormal_max', 5))
            abnormal_min = float(request.form.get('abnormal_min', 0))

            print(f"Received input values -> Window: {window}, Threshold: {threshold}, Max: {abnormal_max}, Min: {abnormal_min}")  # Debugging line

            # Process the stored file using remove_spike function
            plot_files, filtered_data = remove_spike([file_path], window, threshold, abnormal_max, abnormal_min)

            # Save the processed data to a CSV file for download
            processed_filename = f"processed_{os.path.basename(file_path)}.csv"
            processed_file_path = os.path.join(PROCESSED_FOLDER, processed_filename)
            filtered_data.to_csv(processed_file_path, index=False)

            # Add a timestamp to prevent caching
            plot_urls = [f"{url_for('static', filename=f'plots/{p}')}?t={datetime.now().timestamp()}" for p in plot_files]

            return render_template(
                'remove_spike.html',
                plot_urls=plot_urls,
                message=f"Spikes removed successfully! Using file: {os.path.basename(file_path)}",
                stored_filename=os.path.basename(file_path),
                window=window,
                threshold=threshold,
                abnormal_max=abnormal_max,
                abnormal_min=abnormal_min,
                processed_filename=processed_filename  # Pass processed file name to template
            )
        except Exception as e:
            return render_template('remove_spike.html', message=f"Error: {e}")

    return render_template('remove_spike.html', window=2, threshold=0.1, abnormal_max=5, abnormal_min=0)

@app.route('/download_spike_removed/<filename>')
def download_spike_removed(filename):
    """Route to download the processed spike-removed file."""
    processed_file_path = os.path.join(PROCESSED_FOLDER, filename)
    if os.path.exists(processed_file_path):
        return send_file(processed_file_path, as_attachment=True)
    else:
        return "<p style='color: red;'>Processed file not found!</p>", 404

@app.route('/separate_wind_sea_swell', methods=['GET', 'POST'])
def separate_wind_sea_swell():
    """Handle wind-sea-swell separation functionality."""
    if request.method == 'POST':
        # Get uploaded files
        uploaded_files = request.files.getlist('nc_files')
        
        if not uploaded_files or all(file.filename == '' for file in uploaded_files):
            return render_template('separate_wind_sea_swell.html', message="No files selected!")

        # Save uploaded files to a temporary folder
        temp_folder = os.path.join(UPLOAD_FOLDER, "temp_nc_files")
        os.makedirs(temp_folder, exist_ok=True)
        
        saved_files = []
        for file in uploaded_files:
            if file and file.filename.endswith('.nc'):
                filepath = os.path.join(temp_folder, file.filename)
                file.save(filepath)
                saved_files.append(filepath)

        if not saved_files:
            return render_template('separate_wind_sea_swell.html', message="No valid .nc files uploaded!")

        try:
            # Call the windsea_swell_seperation function
            saved_csv_files = windsea_swell_seperation(temp_folder)
            
            # Move CSV files to the PROCESSED_FOLDER
            for csv_file in saved_csv_files:
                filename = os.path.basename(csv_file)
                new_path = os.path.join(PROCESSED_FOLDER, filename)
                os.rename(csv_file, new_path)
            
            return render_template(
                'separate_wind_sea_swell.html',
                message="Wind-sea-swell separation completed!",
                output_files=saved_csv_files,
                basename=path.basename  # Pass the basename function to the template
            )
        except Exception as e:
            return render_template('separate_wind_sea_swell.html', message=f"Error during processing: {e}")
        finally:
            # Clean up temporary files
            for file in saved_files:
                if os.path.exists(file):
                    os.remove(file)
            if os.path.exists(temp_folder):
                os.rmdir(temp_folder)

    return render_template('separate_wind_sea_swell.html')
if __name__ == '__main__':
    app.run(debug=True)