import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend to prevent errors

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

PLOT_FOLDER = "static/plots"  # Folder to save plots

def remove_spike(files, window=2, threshold=0.1, abnormal_max=5, abnormal_min=0):
    plot_files = []  # List to store saved plot filenames
    filtered_data = None  # Store filtered data

    for file in files:
        try:
            print(f"Processing file: {file}")  # Debugging line
            print(f"Applied Parameters -> Window: {window}, Threshold: {threshold}, Max: {abnormal_max}, Min: {abnormal_min}")  # Debugging line
            
            fig, ax = plt.subplots(figsize=(16, 6))

            # Read data
            dat = pd.read_csv(file, header=None)
            dat = dat.rename(columns={0: "Date", 1: "Hs"})
            dat["Date"] = pd.to_datetime(dat["Date"])

            # Remove abnormal values
            dat = dat[(dat["Hs"] >= abnormal_min) & (dat["Hs"] <= abnormal_max)]

            # Compute rolling mean and filter data
            dat['rolling_mean'] = dat["Hs"].rolling(window=window, center=True).mean()
            dat['diff'] = np.abs(dat["Hs"] - dat['rolling_mean'])
            filtered_data = dat[dat['diff'] <= threshold]  # Filter spikes

            # Plot filtered data
            ax.plot(dat["Date"], dat["Hs"], label="Raw Data", color='red')
            ax.plot(filtered_data["Date"], filtered_data["Hs"], label="Filtered Data", color='blue')

            # Customize plot
            ax.set_xlabel("Date")
            ax.set_ylabel("Hs")
            ax.legend()
            ax.set_title(f"Spike Removal - {os.path.basename(file)}")

            # Save plot to file
            plot_filename = f"plot_{os.path.basename(file)}.png"
            plot_path = os.path.join(PLOT_FOLDER, plot_filename)
            plt.savefig(plot_path)
            plt.close(fig)  # Close figure to free memory

            plot_files.append(plot_filename)
        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue

    return plot_files, filtered_data  # Return list of saved plot filenames and filtered data
