import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend to prevent errors

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

PLOT_FOLDER = "static/plots"  # Folder to save plots

def remove_spike(files, window=2, threshold=0.1, abnormal_max=5, abnormal_min=0, plot_folder="static/plots"):
    print("==== remove_spike CALLED ====")
    print("Files received:", files)
    print("Saving plots to:", plot_folder)

    plot_files = []
    filtered_data = None

    os.makedirs(plot_folder, exist_ok=True)

    for file in files:
        try:
            print(f"Processing file: {file}")
            dat = pd.read_csv(file, header=0)
            dat.columns = dat.columns.str.strip()
            dat = dat.rename(columns={"Timestamp": "Date", "Hm0": "Hs"})
            dat["Date"] = pd.to_datetime(dat["Date"])

            dat = dat[(dat["Hs"] >= abnormal_min) & (dat["Hs"] <= abnormal_max)]
            dat['rolling_mean'] = dat["Hs"].rolling(window=window, center=True).mean()
            dat['diff'] = np.abs(dat["Hs"] - dat['rolling_mean'])
            filtered_data = dat[dat['diff'] <= threshold]

            fig, ax = plt.subplots(figsize=(16, 6))
            ax.plot(dat["Date"], dat["Hs"], label="Raw Data", color='red')
            ax.plot(filtered_data["Date"], filtered_data["Hs"], label="Filtered Data", color='blue')
            ax.set_xlabel("Date")
            ax.set_ylabel("Hs")
            ax.legend()
            ax.set_title(f"Spike Removal - {os.path.basename(file)}")

            base = os.path.splitext(os.path.basename(file))[0]  # removes .his
            plot_filename = f"plot_{base}.png"
            plot_path = os.path.join(plot_folder, plot_filename)
            plt.savefig(plot_path)
            plt.close(fig)

            print(f"Plot saved at: {plot_path}")
            print("Exists?", os.path.exists(plot_path))

            if os.path.exists(plot_path):
                plot_files.append(plot_filename)

        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue

    return plot_files, filtered_data

