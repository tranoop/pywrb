pywrb
This is the beta version of a tool for processing Datawell directional wave rider buoy chip data. Currently, it supports the processing of SDT files from the MKIII buoy. The SDT files can be processed to extract buoy spectra and history files, which can then be downloaded. Additionally, the spectral data can be converted to NetCDF format for easier access. A preliminary data quality check has also been incorporated.
I am actively working on improving this tool, and I would greatly appreciate your valuable suggestions and feedback. Please feel free to reach out at anoopoceanography@gmail.com. If anyone is interested in collaborating on this project, I would be happy to discuss further.
Installation
From GitHub
pip install git+https://github.com/tranoop/pywrb.git

From Source

git clone https://github.com/tranoop/pywrb.git

cd pywrb

pip install -e .

Usage
pywrb

Access the web interface at http://127.0.0.1:5000.
Directory Structure

Dependencies

Python >= 3.10
Flask >= 2.0.0
numpy >= 1.21.0
pandas >= 1.3.0
matplotlib >= 3.4.0
netCDF4 >= 1.5.7 (optional for NetCDF conversion)

Contributing
Pull requests are welcome. Please open an issue to discuss proposed changes.

