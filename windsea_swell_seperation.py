import xarray as xr
import pandas as pd
import numpy as np
import glob
import os

def windsea_swell_seperation(folder_path):
    """
    Process wave data from .nc files in the specified folder.

    Parameters:
        folder_path (str): Path to the folder containing .nc files.

    Returns:
        list: A list of file paths for the saved CSV files.
    """
    files = glob.glob(f"{folder_path}/*.nc")  # Get all .nc files in the folder
    saved_csv_files = []  # List to store paths of saved CSV files

    for file in files:
        results = pd.DataFrame(columns=["Date", "Hs_swell", "Hs_sea"])  # Initialize an empty DataFrame
        data = xr.open_dataset(file)
        date = pd.to_datetime(data.time.values)  # Convert date array to datetime
        S = data.SmaxXpsd.values  # Extract SmaxXpsd array
        f = data.Frequency.values  # Extract frequency array
        spec = (S[:, 1:] + S[:, :63]) * 0.5
        freq = (f[1:] + f[:63]) * 0.5
        df = np.diff(f)
        fup_indices = np.where(freq <= 0.5)[0]
        fup = freq[fup_indices]

        for i in range(len(S)):
            spec_row = spec[i, :]
            m1fstar = np.zeros(len(fup))
            mminus1fstar = np.zeros(len(fup))
            time = date[i]

            for j in range(len(fup)):
                m1fstar[j] = np.sum(spec_row[j:len(fup)] * freq[j:len(fup)] ** 1 * df[j:len(fup)])
                mminus1fstar[j] = np.sum(spec_row[j:len(fup)] * freq[j:len(fup)] ** (-1) * df[j:len(fup)])

            with np.errstate(invalid="ignore", divide="ignore"):
                alfafstar = m1fstar / np.sqrt(mminus1fstar)

            # Skip if alfafstar is empty or contains only NaN values
            if np.all(np.isnan(alfafstar)) or len(alfafstar) == 0:
                continue

            try:
                loc1 = np.nanargmax(alfafstar)
                fm = fup[loc1]

                fseparation = 24.2084 * fm**3 - 9.2021 * fm**2 + 1.8906 * fm - 0.04286
                spec_trimmed = spec_row[0:len(fup)]
                spec_df = pd.DataFrame(spec_trimmed)
                fup_df = pd.DataFrame(fup)

                f_swell = fup_df[fup_df[0] < fseparation].dropna()
                f_sea = fup_df[fup_df[0] > fseparation].dropna()

                if fseparation > 0.025:
                    df_swell = f_swell.diff()
                    df_sea = f_sea.diff()
                    spec_swell = spec_df.loc[f_swell.index]
                    spec_sea = spec_df.loc[f_sea.index]

                    # Extract scalar values for fswell_peak and fsea_peak
                    fswell_peak = f_swell.loc[spec_swell.idxmax()[0]].values[0]  # Extract scalar value
                    fsea_peak = f_sea.loc[spec_sea.idxmax()[0]].values[0]  # Extract scalar value

                    Hs_swell = 4 * np.sqrt(np.nansum(spec_swell.values.flatten() * df_swell.values.flatten()))
                    Hs_sea = 4 * np.sqrt(np.nansum(spec_sea.values.flatten() * df_sea.values.flatten()))

                    # Append results to the DataFrame
                    results = pd.concat(
                        [results, pd.DataFrame([[time, Hs_swell, Hs_sea]], columns=["Date", "Hs_swell", "Hs_sea"])],
                        ignore_index=True
                    )
            except Exception as e:
                print(f"Error processing file {file}: {e}")
                continue

        # Save results to a CSV file with the same name as the input file
        output_filename = f"{os.path.splitext(os.path.basename(file))[0]}_windsea_swell.csv"
        output_path = os.path.join(folder_path, output_filename)
        results.to_csv(output_path, index=False)
        saved_csv_files.append(output_path)

    return saved_csv_files