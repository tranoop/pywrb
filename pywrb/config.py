import os

class Config:
    SECRET_KEY = 'supersecretkey'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    PROCESSED_FOLDER = os.path.join(BASE_DIR, 'processed')
    CONVERTED_FOLDER = os.path.join(BASE_DIR, 'converted_nc_files')
    TEMP_SPT_FOLDER = os.path.join(BASE_DIR, 'temp_spt_files')
    PLOT_FOLDER = os.path.join(BASE_DIR, 'static', 'plots')
    
    ALLOWED_EXTENSIONS = {'SDT'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
