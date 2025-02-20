from flask import Flask, render_template, request, send_from_directory
import os

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
            return "No file part", 400
        
        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400

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

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

def process_SDT_file(filepath):
    """Process the SDT file and save multiple outputs."""
    filename_base = os.path.splitext(os.path.basename(filepath))[0]

    output_his = os.path.join(PROCESSED_FOLDER, filename_base + '.his')
    output_csv = os.path.join(PROCESSED_FOLDER, filename_base + '_225.csv')
    output_txt = os.path.join(PROCESSED_FOLDER, filename_base + '_SPT.txt')

    with open(output_his, 'w') as fod_his, open(output_csv, 'w') as fod_csv, open(output_txt, 'w') as fod_txt:
        fod_his.write("Processing done for .his file.\n")
        fod_csv.write("Processing done for .csv file.\n")
        fod_txt.write("Processing done for .txt file.\n")

    print(f"Processed files saved: {output_his}, {output_csv}, {output_txt}")

if __name__ == '__main__':
    app.run(debug=True)
