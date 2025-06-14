
import webbrowser
from threading import Timer
from flask import (Flask, render_template, request, send_from_directory, 
                  send_file, url_for, session, jsonify, current_app)
import os
import pandas as pd
import numpy as np
import glob
import zipfile
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
from os import path

# Import processing functions from your package
from .processing.process_SDT_file import process_SDT_file
from .processing.SPT_to_NC import convert_spt_to_nc
from .processing.remove_spike import remove_spike
from .processing.windsea_swell_seperation import windsea_swell_seperation
from .processing.calculate_drift_velocity import calculate_drift_velocity

def create_app():
    """Factory function to create and configure the Flask application"""
    app = Flask(__name__)
    app.secret_key = 'supersecretkey'

    # Configuration
    app.config.update({
        'UPLOAD_FOLDER': os.path.join(os.getcwd(), 'uploads'),
        'PROCESSED_FOLDER': os.path.join(os.getcwd(), 'processed'),
        'CONVERTED_FOLDER': os.path.join(os.getcwd(), 'converted_nc_files'),
        'TEMP_SPT_FOLDER': os.path.join(os.getcwd(), 'temp_spt_files'),
        'PLOT_FOLDER': os.path.join(os.getcwd(), 'static', 'plots')
    })

    # Ensure directories exist
    with app.app_context():
        for folder in [
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['PROCESSED_FOLDER'],
            current_app.config['CONVERTED_FOLDER'],
            current_app.config['TEMP_SPT_FOLDER'],
            current_app.config['PLOT_FOLDER']
        ]:
            os.makedirs(folder, exist_ok=True)

    # Register routes
    register_routes(app)

    return app
def open_browser():
    """Open the default browser to the Flask app URL"""
    webbrowser.open_new('http://127.0.0.1:5000/')
def register_routes(app):
    """Register all route blueprints with the application"""
    
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        if request.method == 'POST':
            files = request.files.getlist('files')
            if not files or all(file.filename == '' for file in files):
                return "<p style='color: red;'>No files selected!</p>", 400

            uploaded_files = []
            for file in files:
                if file and file.filename.endswith('.SDT'):
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filepath)
                    uploaded_files.append(file.filename)

            return "<p>Files uploaded successfully: " + ", ".join(uploaded_files) + "</p>"
        return render_template('upload.html')

    @app.route('/process', methods=['GET', 'POST'])
    def process():
        files = os.listdir(current_app.config['UPLOAD_FOLDER'])
        
        if request.method == 'POST':
            selected_files = request.form.getlist('files[]')
            if not selected_files:
                return "<p style='color: red;'>No files selected for processing.</p>", 400

            # Clear old processed files
            for old_file in os.listdir(current_app.config['PROCESSED_FOLDER']):
                os.remove(os.path.join(current_app.config['PROCESSED_FOLDER'], old_file))
            
            for filename in selected_files:
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    process_SDT_file(filepath)
                    os.remove(filepath)
                else:
                    return f"<p style='color: red;'>File {filename} not found!</p>", 400

            return "<p>Files processed successfully!</p>"
        return render_template('process.html', files=files)

    @app.route('/save_output')
    def save_output():
        processed_files = os.listdir(current_app.config['PROCESSED_FOLDER'])
        return render_template('save_output.html', processed_files=processed_files)

    @app.route('/download/<filename>')
    def download(filename):
        return send_from_directory(current_app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

    @app.route('/download_all')
    def download_all():
        processed_files = os.listdir(current_app.config['PROCESSED_FOLDER'])
        if not processed_files:
            return "<p style='color: red;'>No processed files available to download.</p>", 400

        zip_path = os.path.join(current_app.config['PROCESSED_FOLDER'], "processed_files.zip")
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in processed_files:
                    file_path = os.path.join(current_app.config['PROCESSED_FOLDER'], file)
                    zipf.write(file_path, file)
            return send_file(zip_path, as_attachment=True)
        except Exception as e:
            return f"<p style='color: red;'>Error creating ZIP file: {e}</p>", 500

    @app.route('/convert_spt', methods=['GET', 'POST'])
    def convert_spt():
        if request.method == 'POST':
            uploaded_files = request.files.getlist('spt_files')
            if not uploaded_files:
                return render_template('convert_spt.html', message="No SPT files selected!")

            os.makedirs(current_app.config['CONVERTED_FOLDER'], exist_ok=True)
            os.makedirs(current_app.config['TEMP_SPT_FOLDER'], exist_ok=True)

            # Save uploaded files
            for file in uploaded_files:
                file_path = os.path.join(current_app.config['TEMP_SPT_FOLDER'], file.filename)
                file.save(file_path)

            try:
                convert_spt_to_nc(current_app.config['TEMP_SPT_FOLDER'], current_app.config['CONVERTED_FOLDER'])
                converted_files = os.listdir(current_app.config['CONVERTED_FOLDER'])
                if converted_files:
                    return render_template('convert_spt.html', message="Conversion completed! You can now download the files.")
                else:
                    return render_template('convert_spt.html', message="No NetCDF files were created. Please check input data.")
            except Exception as e:
                return render_template('convert_spt.html', message=f"Error during conversion: {e}")

        return render_template('convert_spt.html')

    @app.route('/download_nc_all')
    def download_nc_all():
        netcdf_files = os.listdir(current_app.config['CONVERTED_FOLDER'])
        if not netcdf_files:
            return "<p style='color: red;'>No NetCDF files available to download.</p>", 400

        zip_path = os.path.join(current_app.config['CONVERTED_FOLDER'], "converted_nc_files.zip")
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in netcdf_files:
                    file_path = os.path.join(current_app.config['CONVERTED_FOLDER'], file)
                    zipf.write(file_path, file)
            return send_file(zip_path, as_attachment=True)
        except Exception as e:
            return f"<p style='color: red;'>Error creating ZIP file: {e}</p>", 500

    @app.route('/delete_all', methods=['POST'])
    def delete_all():
        try:
            for folder in [
                current_app.config['PROCESSED_FOLDER'],
                current_app.config['CONVERTED_FOLDER'],
                current_app.config['TEMP_SPT_FOLDER'],
                current_app.config['UPLOAD_FOLDER'],
                current_app.config['PLOT_FOLDER']
            ]:
                for file in os.listdir(folder):
                    file_path = os.path.join(folder, file)
                    os.remove(file_path)
            return jsonify({"message": "Automatically generated files deleted successfully!"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/remove_spike', methods=['GET', 'POST'])
    def remove_spike_route():
        file_path = session.get('uploaded_his_file')
        if request.method == 'POST':
            uploaded_files = request.files.getlist('his_files')
            if uploaded_files and uploaded_files[0].filename != '':
                file = uploaded_files[0]
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                session['uploaded_his_file'] = file_path

            if not file_path or not os.path.exists(file_path):
                return render_template('remove_spike.html', message="Error: No file uploaded!")

            try:
                window = int(request.form.get('window', 2))
                threshold = float(request.form.get('threshold', 0.1))
                abnormal_max = float(request.form.get('abnormal_max', 5))
                abnormal_min = float(request.form.get('abnormal_min', 0))

                plot_files, filtered_data = remove_spike([file_path], window, threshold, abnormal_max, abnormal_min)
                processed_filename = f"processed_{os.path.basename(file_path)}.csv"
                processed_file_path = os.path.join(current_app.config['PROCESSED_FOLDER'], processed_filename)
                filtered_data.to_csv(processed_file_path, index=False)

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
                    processed_filename=processed_filename
                )
            except Exception as e:
                return render_template('remove_spike.html', message=f"Error: {e}")

        return render_template('remove_spike.html', window=2, threshold=0.1, abnormal_max=5, abnormal_min=0)

    @app.route('/download_spike_removed/<filename>')
    def download_spike_removed(filename):
        processed_file_path = os.path.join(current_app.config['PROCESSED_FOLDER'], filename)
        if os.path.exists(processed_file_path):
            return send_file(processed_file_path, as_attachment=True)
        return "<p style='color: red;'>Processed file not found!</p>", 404

    @app.route('/separate_wind_sea_swell', methods=['GET', 'POST'])
    def separate_wind_sea_swell():
        if request.method == 'POST':
            uploaded_files = request.files.getlist('nc_files')
            if not uploaded_files or all(file.filename == '' for file in uploaded_files):
                return render_template('separate_wind_sea_swell.html', message="No files selected!")

            temp_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], "temp_nc_files")
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
                saved_csv_files = windsea_swell_seperation(temp_folder)
                for csv_file in saved_csv_files:
                    filename = os.path.basename(csv_file)
                    new_path = os.path.join(current_app.config['PROCESSED_FOLDER'], filename)
                    os.rename(csv_file, new_path)
                
                return render_template(
                    'separate_wind_sea_swell.html',
                    message="Wind-sea-swell separation completed!",
                    output_files=saved_csv_files,
                    basename=path.basename
                )
            except Exception as e:
                return render_template('separate_wind_sea_swell.html', message=f"Error during processing: {e}")
            finally:
                for file in saved_files:
                    if os.path.exists(file):
                        os.remove(file)
                if os.path.exists(temp_folder):
                    os.rmdir(temp_folder)

        return render_template('separate_wind_sea_swell.html')

    @app.route('/download_all_wind_sea_swell')
    def download_all_wind_sea_swell():
        csv_files = [f for f in os.listdir(current_app.config['PROCESSED_FOLDER']) if f.endswith('_windsea_swell.csv')]
        if not csv_files:
            return "<p style='color: red;'>No wind-sea-swell separated CSV files available to download.</p>", 400

        zip_path = os.path.join(current_app.config['PROCESSED_FOLDER'], "windsea_swell_files.zip")
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in csv_files:
                    file_path = os.path.join(current_app.config['PROCESSED_FOLDER'], file)
                    zipf.write(file_path, file)
            return send_file(zip_path, as_attachment=True)
        except Exception as e:
            return f"<p style='color: red;'>Error creating ZIP file: {e}</p>", 500

    @app.route('/stokes_drift', methods=['GET', 'POST'])
    def stokes_drift():
        if request.method == 'POST':
            uploaded_files = request.files.getlist('nc_files')
            max_depth = int(request.form.get('max_depth', 100))
            
            if not uploaded_files or all(file.filename == '' for file in uploaded_files):
                return render_template('stokes_drift.html', message="No NetCDF files selected!")

            temp_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], "temp_stokes")
            os.makedirs(temp_folder, exist_ok=True)
            processed_files = []

            try:
                for file in uploaded_files:
                    if file and file.filename.endswith('.nc'):
                        file_path = os.path.join(temp_folder, file.filename)
                        file.save(file_path)
                        result = calculate_drift_velocity(file_path, max_depth)
                        output_filename = f"stokes_drift_{os.path.splitext(file.filename)[0]}.csv"
                        output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
                        result.to_csv(output_path, index=False)
                        processed_files.append(output_filename)

                if processed_files:
                    return render_template('stokes_drift.html', 
                                        message="Stokes drift calculation completed!",
                                        processed_files=processed_files)
                return render_template('stokes_drift.html', 
                                    message="No valid NetCDF files were processed.")
            except Exception as e:
                return render_template('stokes_drift.html', 
                                    message=f"Error during processing: {str(e)}")
            finally:
                for file in os.listdir(temp_folder):
                    os.remove(os.path.join(temp_folder, file))
                os.rmdir(temp_folder)

        return render_template('stokes_drift.html')

    @app.route('/download_stokes/<filename>')
    def download_stokes(filename):
        return send_from_directory(current_app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

    @app.route('/download_all_stokes')
    def download_all_stokes():
        stokes_files = [f for f in os.listdir(current_app.config['PROCESSED_FOLDER']) if f.startswith('stokes_drift_')]
        if not stokes_files:
            return "<p style='color: red;'>No stokes drift files available to download.</p>", 400

        zip_path = os.path.join(current_app.config['PROCESSED_FOLDER'], "stokes_drift_files.zip")
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in stokes_files:
                    file_path = os.path.join(current_app.config['PROCESSED_FOLDER'], file)
                    zipf.write(file_path, file)
            return send_file(zip_path, as_attachment=True)
        except Exception as e:
            return f"<p style='color: red;'>Error creating ZIP file: {e}</p>", 500

def main():
    """Entry point for running the application"""
    app = create_app()
    
    # Open browser after 1 second delay
    Timer(1, open_browser).start()
    
    app.run(debug=True)

if __name__ == '__main__':
    main()
