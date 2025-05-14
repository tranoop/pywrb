import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def calculate_drift_velocity(nc_file_path, maximum_depth=100):
    """
    Calculate stock_drift velocity from wave spectrum data.
    
    Parameters:
    -----------
    nc_file_path : str
        Path to the netCDF file containing wave spectrum data
    maximum_depth : int, optional
        Maximum depth to calculate drift velocities for (default: 100)
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing drift velocities at different depths for each time step,
        with time in the first column
    """
    # Load data
    dat = xr.open_dataset(nc_file_path)
    f = dat.Frequency.values  # Convert to numpy array upfront
    s = dat.SmaxXpsd.values  # Convert to numpy array upfront
    time = dat.time.values
    
    # Constants
    c = (16 * (np.pi)**3) / 9.8
    depths = np.arange(0, -maximum_depth, -1)  # Predefine depths

    # Precompute frequency-related terms that don't change in loops
    f3 = f**3
    # Compute frequency differences (df)
    df = np.diff(f)
    df = np.append(df, df[-1])  # Pad last value to maintain length

    # Compute rolling mean of frequencies
    fr = (f[:-1] + f[1:]) / 2
    fr = np.append(fr, fr[-1])  # Pad last value

    # Initialize output array with correct shape
    drift_all = np.zeros((len(time), len(depths)))

    for i in range(len(time)):
        spec = s[i]  # Current spectrum
        # Compute rolling mean of spectrum
        spec_rolled = (spec[:-1] + spec[1:]) / 2
        spec_rolled = np.append(spec_rolled, spec_rolled[-1])
        
        for z_idx, z in enumerate(depths):
            # Compute exponential term
            e = np.exp(((8 * (np.pi**2) * f**2) / 9.8) * z)
            
            # Compute drift velocity
            integrand = c * f3 * spec_rolled * e * df
            uz = np.sum(integrand)
            drift_all[i, z_idx] = np.round(uz, 3)
    
    # Convert to DataFrame
    drift_all = pd.DataFrame(drift_all)
    time = pd.DataFrame(time)
    time.columns = ["Date"]
    data = pd.concat([time, drift_all], axis=1)
    
    return data

# Example usage:
# result = calculate_drift_velocity("Vizag_000001_S02-2012_SPT.nc")
# print(result.head())