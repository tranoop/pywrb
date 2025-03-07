import glob
import pandas as pd
import numpy as np
import xarray as xr
import os

def convert_spt_to_nc(input_folder, output_folder):
    """
    Convert multiple *_SPT.txt files in a folder to NetCDF (.nc) format.
    
    Parameters:
        input_folder (str): Path to the folder containing SPT text files.
        output_folder (str): Path to the folder where NetCDF files will be saved.
    """
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all *_SPT.txt files in the input folder
    spt_files = glob.glob(os.path.join(input_folder, "*_SPT.txt"))
    
    for spt in spt_files:
        try:
            print(f"Processing {spt}...")
            spt_data = pd.read_csv(spt, header=None)
            
            # Extract time stamps
            pattern = r'Time Stamp= \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
            matching_indices = spt_data[spt_data[0].str.contains(pattern, na=False)].index
            date = spt_data.iloc[matching_indices]
            date = date[0].str.extract(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
            date.reset_index(inplace=True)
            
            # Add last boundary index
            matching_indices = matching_indices.append(pd.Index([matching_indices[-1] + 65]))
            
            # Separate spectra into individual blocks
            spect = [spt_data.iloc[matching_indices[i] + 1:matching_indices[i + 1]].values.tolist() 
                     for i in range(0, len(matching_indices) - 1)]
            
            datasets = []
            for i in range(len(spect)):
                data_values = pd.DataFrame(spect[i])
                data_values = data_values[0].str.split("\t", expand=True)
                data_values.columns = ["Frequency", "SmaxXpsd", "dir_angle", "spr", "skw",
                                       "kurt", "m2", "n2", "K", "Lat", "Lon"]
                
                # Convert to numeric where possible
                data_values = data_values.apply(pd.to_numeric, errors='coerce')
                data_values.set_index("Frequency", inplace=True)
                
                # Convert to xarray Dataset
                data_xr = xr.Dataset.from_dataframe(data_values)
                data_xr = data_xr.assign_coords(time=pd.to_datetime(date.iloc[i, 1]))
                
                # Add variable attributes
                data_xr["SmaxXpsd"].attrs = {"units": "unit1", "long_name": "Spectral Max Power Density"}
                data_xr["dir_angle"].attrs = {"units": "degrees", "long_name": "Direction Angle"}
                data_xr["spr"].attrs = {"units": "degrees", "long_name": "Spread"}
                data_xr["skw"].attrs = {"units": "unit2", "long_name": "Skewness"}
                data_xr["kurt"].attrs = {"units": "unit3", "long_name": "Kurtosis"}
                data_xr["m2"].attrs = {"units": "m^2", "long_name": "Moment Order 2"}
                data_xr["n2"].attrs = {"units": "n_unit", "long_name": "Some Variable N2"}
                data_xr["K"].attrs = {"units": "kelvin", "long_name": "Constant K"}
                data_xr["Lat"].attrs = {"units": "degrees_north", "long_name": "Latitude"}
                data_xr["Lon"].attrs = {"units": "degrees_east", "long_name": "Longitude"}
                
                datasets.append(data_xr)
            
            # Combine all time-based datasets
            combined_data_xr = xr.concat(datasets, dim="time")
            combined_data_xr.attrs = {
                "title": "Spectral Data Analysis",
                "description": "Spectral data including frequency-based metrics with timestamps",
                "units_note": "Units and descriptions for each variable can be found in variable attributes",
            }
            
            # Save NetCDF
            output_filename = os.path.join(output_folder, os.path.basename(spt).replace(".txt", ".nc"))
            combined_data_xr.to_netcdf(output_filename)
            print(f"Successfully converted {spt} to {output_filename}")
        
        except Exception as e:
            print(f"Error processing {spt}: {e}")

# Example usage
# convert_spt_to_nc("path/to/spt_files", "path/to/output_nc")