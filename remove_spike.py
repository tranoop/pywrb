import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

PLOT_FOLDER = "static/plots"
os.makedirs(PLOT_FOLDER, exist_ok=True)  # ✅ Ensure plot folder exists

def remove_spike(files, window=2, threshold=0.1, abnormal_max=5, abnormal_min=0):
    plot_files = []
    
    for file in files:  # ✅ Iterate over provided list of files
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Read data
        dat = pd.read_csv(file, header=None)
        dat = dat.rename(columns={0: "Date", 1: "Hs"})
        dat["Date"] = pd.to_datetime(dat["Date"])

        # Remove abnormal values
        dat = dat[(dat["Hs"] >= abnormal_min) & (dat["Hs"] <= abnormal_max)]
        
        # Plot raw data
        ax.plot(dat["Date"], dat["Hs"], label="Raw Data", color='red')
        
        # Compute rolling mean and filter data
        dat['rolling_mean'] = dat["Hs"].rolling(window=window, center=True).mean()
        dat['diff'] = np.abs(dat["Hs"] - dat['rolling_mean'])
        filtered_dat = dat[dat['diff'] <= threshold]
        
        # Plot filtered data
        ax.plot(filtered_dat["Date"], filtered_dat["Hs"], label="Spike removed data", color='blue')

        ax.set_xlabel("Date")
        ax.set_ylabel("Hs")
        ax.legend()

        # ✅ Save plot in static folder
        plot_filename = f"plot_{os.path.basename(file)}.png"
        plot_path = os.path.join(PLOT_FOLDER, plot_filename)
        plt.savefig(plot_path)
        plt.close()

        plot_files.append(plot_filename)

    return plot_files  # ✅ Return list of saved plot filenames

