from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import os
import pandas as pd
import xarray as xr

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "<p style='color:red;'>No file part.</p>", 400
        
        file = request.files['file']
        if file.filename == '':
            return "<p style='color:red;'>No selected file.</p>", 400

        if file and file.filename.endswith('.SDT'):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            return "<p>File uploaded successfully.</p>"

    return render_template('upload.html')

@app.route('/process', methods=['GET', 'POST'])
def process():
    files = os.listdir(UPLOAD_FOLDER)

    if request.method == 'POST':
        filename = request.form.get('file')
        if filename:
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            process_SDT_file(filepath)
            return "<p>File processed successfully.</p>"

    return render_template('process.html', files=files)

@app.route('/save_output')
def save_output():
    processed_files = os.listdir(PROCESSED_FOLDER)
    return render_template('save_output.html', processed_files=processed_files)

@app.route('/convert_nc', methods=['GET', 'POST'])
def convert_nc():
    processed_files = os.listdir(PROCESSED_FOLDER)
    spt_files = [f for f in processed_files if f.endswith(".SPT.txt")]
    nc_files = [f for f in processed_files if f.endswith(".nc")]

    if request.method == 'POST':
        filename = request.form.get('file')
        if filename:
            filepath = os.path.join(PROCESSED_FOLDER, filename)
            output_nc = filepath.replace(".txt", ".nc")
            convert_spt_to_nc(filepath, output_nc)
            return "<p>File converted successfully. Go to 'Save Output' to download the NC file.</p>"

    return render_template('convert_nc.html', processed_files=spt_files, nc_files=nc_files)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

def process_SDT_file(filepath):
    """Simulate processing of SDT file and create SPT output."""
    filename_base = os.path.splitext(os.path.basename(filepath))[0]
    output_txt = os.path.join(PROCESSED_FOLDER, filename_base + '_SPT.txt')

    with open(output_txt, 'w') as f:
        f.write("Sample SPT Data\n")  # Placeholder for actual processing

def convert_spt_to_nc(spt_file, output_nc):
    """Convert SPT file to NetCDF format"""
    spt_files = pd.read_csv(spt_file, header=None)

    # Extract timestamps
    pattern = r'Time Stamp= \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    matching_indices = spt_files[spt_files[0].str.contains(pattern, na=False)].index
    date = spt_files.iloc[matching_indices]
    date = date[0].str.extract(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
    date.reset_index(inplace=True)

    # Process spectral data
    datasets = []
    for i in range(len(matching_indices) - 1):
        data_values = pd.DataFrame(spt_files.iloc[matching_indices[i] + 1:matching_indices[i + 1]].values)
        data_values = data_values[0].str.split("\t", expand=True)
        data_values.columns = ["Frequency", "SmaxXpsd", "dir_angle", "spr", "skw", "kurt", "m2", "n2", "K", "Lat", "Lon"]
        data_values = data_values.apply(pd.to_numeric, errors='coerce')
        data_xr = xr.Dataset.from_dataframe(data_values.set_index("Frequency"))
        data_xr = data_xr.assign_coords(time=pd.to_datetime(date.iloc[i, 1]))
        datasets.append(data_xr)

    combined_data_xr = xr.concat(datasets, dim="time")
    combined_data_xr.to_netcdf(output_nc)

if __name__ == '__main__':
    app.run(debug=True)
