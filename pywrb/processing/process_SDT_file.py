import os
import numpy as np
import datetime
from flask import current_app

def process_SDT_file(s_file, processed_folder=None):
    """Main function to process the SDT file."""
    if processed_folder is None:
        processed_folder = current_app.config['PROCESSED_FOLDER']
    
    # Ensure processed folder exists
    os.makedirs(processed_folder, exist_ok=True)
    
    filename_base = os.path.splitext(os.path.basename(s_file))[0]

    # Define output file paths
    s_out = os.path.join(processed_folder, filename_base + '.his')
    s_out4 = os.path.join(processed_folder, filename_base + '_225.csv')
    s_out5 = os.path.join(processed_folder, filename_base + '_SPT.txt')

    if os.path.exists(s_file):
        nb = 0
        nspt = 0

        with open(s_file, 'rb') as fid, open(s_out, 'w') as fod, open(s_out4, 'w') as fod4, open(s_out5, 'w') as fid_spt:
            # Write header to .his file
            fod.write("Timestamp, Hm0, TI, TE, T1, Tz, T3, T4, Tref, Tsea, Bat\n")

            while True:
                hdr, tms = read_header(fid)
                nb += 5
                if tms.size == 0:
                    break
                
                dt = parse_timestamp(tms)
                bspt, bsys, chks = read_data(fid)
                b = np.concatenate((tms, bspt, bsys, chks))
                cs = calculate_checksum(b)

                if cs == 0:
                    sys = parse_system_data(bsys)
                    spt = parse_spectral_data(bspt)

                    nspt += 1
                    mom, mom2 = calculate_moments(spt)

                    # Calculate parameters based on moments
                    Hm0 = 4 * np.sqrt(mom[3])
                    TI = np.sqrt(mom[1] / mom[3])
                    TE = mom[2] / mom[3]
                    T1 = mom[3] / mom[4]
                    Tz = np.sqrt(mom[3] / mom[5])
                    T3 = np.sqrt(mom[4] / mom[6])
                    T4 = (mom[4] / mom[7]) ** 0.5

                    prms = [Hm0, TI, TE, T1, Tz, T3, T4]
                    prms4 = [H for H in [Hm0, TI, TE, T1, Tz, T3, T4] + sys[4:]]
                    write_output(dt, prms, prms4, sys, spt, fod, fod4, fid_spt)

        print(f"Processed files saved: {s_out}, {s_out4}, {s_out5}")
        # Verify files exist
        for file_path in [s_out, s_out4, s_out5]:
            print(f"File {file_path} exists: {os.path.exists(file_path)}")
    else:
        print(f"{s_file} does not exist.")

def read_header(fid):
    """Read header and timestamp from the file."""
    hdr = np.fromfile(fid, dtype=np.uint8, count=5)
    tms = np.fromfile(fid, dtype=np.uint8, count=6)
    return hdr, tms

def parse_timestamp(tms):
    """Parse timestamp bytes into a datetime object."""
    year = int(tms[0]) * 256 + int(tms[1])
    month = tms[2]
    day = tms[3]
    hour = tms[4]
    minute = tms[5]
    return datetime.datetime(year, month, day, hour, minute)

def read_data(fid):
    """Read the various data segments from the file."""
    bspt = np.fromfile(fid, dtype=np.uint8, count=512)
    bsys = np.fromfile(fid, dtype=np.uint8, count=32)
    chks = np.fromfile(fid, dtype=np.uint8, count=1)
    return bspt, bsys, chks

def calculate_checksum(data):
    """Calculate the checksum for the given data."""
    cs = data[0]
    for j in range(1, len(data)):
        cs ^= data[j]
    return cs

def parse_system_data(bsys):
    """Parse system data bytes into meaningful parameters."""
    global Smax, Lat, Lon

    GPS = (int(bsys[1]) // 16) % 8
    Hm0 = ((int(bsys[2]) * 256 + int(bsys[3])) % 4096) / 100
    Tz = 400 / ((int(bsys[4]) * 256 + int(bsys[5])) % 256)
    Smax = np.exp(-0.005 * ((int(bsys[6]) * 256 + int(bsys[7])) % 4096)) * 5000
    Tref = ((int(bsys[8]) * 256 + int(bsys[9])) % 1024) / 20 - 5
    Tsea = ((int(bsys[10]) * 256 + int(bsys[11])) % 1024) / 20 - 5
    Bat = int(bsys[12]) % 8
    BLE = ((int(bsys[12]) * 256 + int(bsys[13])) // 16) % 256
    Av = (int(bsys[14]) * 256 + int(bsys[15])) % 4096
    Av = (2048 - Av if Av > 2048 else Av) / 800
    Ax = (int(bsys[16]) * 256 + int(bsys[17])) % 4096
    Ax = (2048 - Ax if Ax > 2048 else Ax) / 800
    Ay = (int(bsys[18]) * 256 + int(bsys[19])) % 4096
    Ay = (2048 - Ay if Ay > 2048 else Ay) / 800

    Lat = (((int(bsys[20]) % 16) * 256 + int(bsys[21])) * 16 + (int(bsys[22]) % 16)) * 256 + int(bsys[23])
    Lat = (Lat % (2**24)) / (2**23) * 90
    Lat = 90 - Lat if Lat > 90 else Lat

    Lon = (((int(bsys[24]) % 16) * 256 + int(bsys[25])) * 16 + (int(bsys[26]) % 16)) * 256 + int(bsys[27])
    Lon = (Lon % (2**24)) / (2**23) * 180
    Lon = 180 - Lon if Lon > 180 else Lon

    ori = ((int(bsys[28]) * 256 + int(bsys[29])) % 4096) * 360 / 256
    incl = (int(bsys[31]) + (int(bsys[30]) % 16) / 16) * 360 / 256 / 2 - 90

    return [Hm0, Tz, Smax, Tref, Tsea, Bat, BLE, Av, Ax, Ay, GPS, Lat, Lon, ori, incl]

def parse_spectral_data(bspt):
    """Parse spectral data bytes into a structured format."""
    spt = []
    for j in range(0, len(bspt), 8):
        jf = int(bspt[j]) % 64
        frq = jf * 0.005 + 0.025 if jf < 16 else jf * 0.01 - 0.05
        sprlsb = int(bspt[j]) // 64
        dir_angle = int(bspt[j + 1]) * 360 / 256
        psd = np.exp(-0.005 * ((int(bspt[j + 2]) * 256 + int(bspt[j + 3])) % 4096))
        n2lsb = (int(bspt[j + 2]) // 16) % 4
        m2lsb = int(bspt[j + 2]) // 64
        spr = (int(bspt[j + 4]) + sprlsb / 4) * 360 / 256 / np.pi
        m2 = (int(bspt[j + 5]) + m2lsb / 4) / 128 - 1
        n2 = (int(bspt[j + 6]) + n2lsb / 4) / 128 - 1
        K = int(bspt[j + 7]) * 0.01
        sgmc = spr * np.pi / 180
        m1 = 1 - sgmc**2 / 2
        sgmca = np.sqrt((1 - m2) / 2)
        skw = -n2 / sgmca**3
        kurt = (6 - 8 * m1 + 2 * m2) / sgmc**4
        spt.append([frq, Smax * psd, dir_angle, spr, skw, kurt, m2, n2, K, Lat, Lon])
    return spt

def calculate_moments(spt):
    """Calculate statistical moments from spectral data."""
    mom = np.zeros(8)
    mom2 = np.zeros(14)
    frq = [inner_list[0] for inner_list in spt]
    psd = [inner_list[1] for inner_list in spt]

    o = 3
    oo = 5
    for j in range(1, len(frq)):
        for n in range(-2, 5):
            yj1 = psd[j - 1] * frq[j - 1] ** n
            yj = psd[j] * frq[j] ** n
            mom[o + n] += 0.5 * (yj + yj1) * (frq[j] - frq[j - 1])
        for n in range(-4, 9):
            yj1 = psd[j - 1] ** 2 * frq[j - 1] ** n
            yj = psd[j] ** 2 * frq[j] ** n
            mom2[oo + n] += 0.5 * (yj + yj1) * (frq[j] - frq[j - 1])

    return mom, mom2

def write_output(dts, prms, prms4, sys, spt, fod, fod4, fid_spt):
    """Write output data to files."""
    # Write to .his file
    fod.write(f"{dts}, {', '.join(f'{p:.2f}' for p in prms)}, "
              f"{sys[4]:.2f}, {sys[5]:.2f}, {sys[6]}\n")
    
    # Write to _225.csv file
    formatted_values = "\t".join(f"{p:.2f}" for p in prms4)  # Format values first
    fod4.write(f"{dts}\t{formatted_values}\n")  # Then use f-string

    # Write to _SPT.txt file
    fid_spt.write(f"Time Stamp= {dts}\n")
    for row in spt:
        fid_spt.write("\t".join(f"{val:.3f}" for val in row) + "\n")

