#!/usr/bin/env python3
'''
Plot input noise after thermal cycling ATLAS ITk strips barrel modules

Usage:
python plot_combined_inputnoise_noskip_UCSC.py -i 'UCSC/HX/SN20USBHX2002099/SN20USBHX2002099_*.json'
python plot_combined_inputnoise_noskip_UCSC.py -i 'UCSC/HX/SN*/*.json'
'''

import os
import json
import csv
import glob
import argparse
from datetime import datetime
from collections import defaultdict

import numpy as np
import matplotlib as mplt
mplt.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm


# ============================================================
# Global error summary
# ============================================================

error_summary = {
    "B": [],
    "C": [],
    "D": [],
    "E": [],
}


# ============================================================
# Helper functions
# ============================================================

def flatten(input_data):
    if isinstance(input_data, list) and all(isinstance(x, (int, float)) for x in input_data):
        return input_data

    if isinstance(input_data, list) and all(isinstance(x, list) for x in input_data):
        return [item for sublist in input_data for item in sublist]

    raise TypeError(f"Expected list of numbers or list of lists, got {type(input_data)}")


def json_to_dict(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def mkdir(path):
    os.makedirs(path, exist_ok=True)


def clean_serial(serial):
    return serial[2:] if serial.startswith("SN") else serial


def ensure_sn(serial):
    serial = str(serial)
    return serial if serial.startswith("SN") else f"SN{serial}"


def parse_timestamp(ts_str):
    try:
        ts_str = str(ts_str).replace("T", " ").replace("Z", "").split(".")[0].strip()
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min


def get_module_from_path(file_path):
    parts = os.path.normpath(file_path).split(os.sep)

    for part in parts:
        if part.startswith("SN20USB"):
            return part

    basename = os.path.basename(file_path)
    return os.path.splitext(basename)[0].split("_")[0]


def safe_get_module_name(file_path):
    try:
        data = json_to_dict(file_path)
        return data.get("properties", {}).get("det_info", {}).get("name", None)
    except Exception:
        return None


def get_module_name(file_path):
    module_name = safe_get_module_name(file_path)

    if module_name:
        return ensure_sn(module_name.replace("SN", ""))

    return get_module_from_path(file_path)


def get_base_output_dir(input_files, fallback_output="UCSC/HX3"):
    if not input_files:
        return fallback_output

    first_file = os.path.normpath(input_files[0])
    parts = first_file.split(os.sep)

    if "UCSC" in parts:
        idx = parts.index("UCSC")

        if idx + 1 < len(parts):
            return os.path.join(parts[idx], parts[idx + 1])

    return fallback_output


def add_error(category, module_name, file_path, message, count=None, values=None, stream=None):
    error_summary[category].append({
        "module": module_name or "Unknown",
        "file": os.path.basename(file_path) if file_path else "N/A",
        "stream": stream or "N/A",
        "message": message,
        "count": count,
        "values": values or [],
    })


# ============================================================
# File handling
# ============================================================

def filter_input_files(infiles, keep_fit_code=4):
    print(f"\nFiltering to keep fit_type_code = {keep_fit_code}")

    kept = []

    for f in infiles:
        try:
            data = json_to_dict(f)
            module_name = get_module_name(f)
            fit_code = data.get("properties", {}).get("fit_type_code")

            if fit_code == keep_fit_code:
                kept.append(f)
            else:
                msg = f"fit_type_code = {fit_code}"
                print(f"❌ CATEGORY D: {os.path.basename(f)} — {msg}")
                add_error("D", module_name, f, f"File skipped: {msg}")

        except Exception as e:
            module_name = get_module_from_path(f)
            msg = f"File skipped or unreadable: {e}"
            print(f"❌ CATEGORY D: {os.path.basename(f)} — {msg}")
            add_error("D", module_name, f, msg)

    print(f"Kept {len(kept)} files")
    print(f"Skipped {len(infiles) - len(kept)} files")

    return kept


def group_files_by_module(files):
    grouped = defaultdict(list)

    for f in files:
        module_name = get_module_name(f)
        grouped[module_name].append(f)

    return dict(grouped)


# ============================================================
# Plot combined histogram
# ============================================================

def plot_combined_stream(json_paths, stream, output_base_dir, module_name):
    file_data = []
    warm_noise_values = []
    cold_noise_values = []
    low_high_summary = []

    result_key = "innse_under" if stream == "under" else "innse_away"

    for path in json_paths:
        filename = os.path.basename(path)

        try:
            data = json_to_dict(path)

            results = data.get("results", {})
            properties = data.get("properties", {})

            if result_key not in results:
                raise KeyError(f"Missing results['{result_key}']")

            noise_raw = results[result_key]

            if noise_raw is None:
                raise ValueError("noise data is None")

            noise = flatten(noise_raw)
            noise = np.array(noise, dtype=float)

            if len(noise) == 0:
                raise ValueError("noise array is empty")

            low_vals = [float(val) for val in noise if val < 600]
            high_vals = [float(val) for val in noise if val > 1100]

            if high_vals:
                msg = f"{filename} — high_count = {len(high_vals)}, high_values = {high_vals}"
                print(f"⚠️ CATEGORY B: {msg}")
                add_error(
                    "B",
                    module_name,
                    path,
                    msg,
                    count=len(high_vals),
                    values=high_vals,
                    stream=stream,
                )

            if low_vals:
                msg = f"{filename} — low_count = {len(low_vals)}, low_values = {low_vals}"
                print(f"⚠️ CATEGORY C: {msg}")
                add_error(
                    "C",
                    module_name,
                    path,
                    msg,
                    count=len(low_vals),
                    values=low_vals,
                    stream=stream,
                )

            if low_vals or high_vals:
                low_high_summary.append({
                    "filename": filename,
                    "stream": stream,
                    "low_count": len(low_vals),
                    "low_values": low_vals,
                    "high_count": len(high_vals),
                    "high_values": high_vals,
                })

            dcs = properties.get("DCS", {})
            temp = float(dcs.get("AMAC_NTCpb", 999))

            raw_time = data.get("timestamp", data.get("date", ""))
            timestamp = (
                str(raw_time)
                .replace("T", " ")
                .replace("Z", "")
                .split(".")[0]
                .strip()
                if raw_time
                else None
            )

            file_data.append({
                "file": filename,
                "temp": temp,
                "noise": noise,
                "timestamp": timestamp,
            })

            if temp > 10:
                warm_noise_values.extend(noise)
            else:
                cold_noise_values.extend(noise)

        except Exception as e:
            msg = f"{filename} — {e}"
            print(f"❌ CATEGORY D: {msg}")
            add_error("D", module_name, path, msg)

    if not file_data:
        msg = f"No valid histogram data for {module_name}, stream {stream}"
        print(f"❌ CATEGORY E: {msg}")
        add_error("E", module_name, None, msg)
        return False

    cold_data = sorted(
        [d for d in file_data if d["temp"] <= 10],
        key=lambda x: parse_timestamp(x["timestamp"]),
    )

    warm_data = sorted(
        [d for d in file_data if d["temp"] > 10],
        key=lambda x: parse_timestamp(x["timestamp"]),
    )

    cold_cmap = cm.get_cmap("Blues", max(len(cold_data), 1))
    warm_cmap = cm.get_cmap("Oranges", max(len(warm_data), 1))

    cold_mean, cold_std = (
        (np.mean(cold_noise_values), np.std(cold_noise_values))
        if cold_noise_values
        else (np.nan, np.nan)
    )

    warm_mean, warm_std = (
        (np.mean(warm_noise_values), np.std(warm_noise_values))
        if warm_noise_values
        else (np.nan, np.nan)
    )

    plt.figure(figsize=(14, 6))

    legend_entries = []
    first_timestamp = next((d["timestamp"] for d in file_data if d["timestamp"]), None)

    for i, entry in enumerate(cold_data):
        color = cold_cmap(i)
        mean_val = np.mean(entry["noise"])
        std_val = np.std(entry["noise"])

        label = f"cold_{i + 1:02d} T={entry['temp']:.1f}C | mu={mean_val:.1f}, sigma={std_val:.1f}"

        plt.hist(
            entry["noise"],
            bins=40,
            alpha=0.5,
            color=color,
            edgecolor="black",
            linewidth=0.3,
        )

        plt.axvline(
            mean_val,
            color=color,
            linestyle="dashed",
            linewidth=1,
        )

        legend_entries.append(label)

    for i, entry in enumerate(warm_data):
        color = warm_cmap(i)
        mean_val = np.mean(entry["noise"])
        std_val = np.std(entry["noise"])

        label = f"warm_{i + 1:02d} T={entry['temp']:.1f}C | mu={mean_val:.1f}, sigma={std_val:.1f}"

        plt.hist(
            entry["noise"],
            bins=40,
            alpha=0.5,
            color=color,
            edgecolor="black",
            linewidth=0.3,
        )

        plt.axvline(
            mean_val,
            color=color,
            linestyle="dashed",
            linewidth=1,
        )

        legend_entries.append(label)

    if not np.isnan(cold_mean):
        plt.axvline(
            cold_mean,
            color="blue",
            linestyle="dashed",
            linewidth=2.5,
        )
        legend_entries.append(f"All Cold mu={cold_mean:.1f}, sigma={cold_std:.1f}")

    if not np.isnan(warm_mean):
        plt.axvline(
            warm_mean,
            color="orange",
            linestyle="dashed",
            linewidth=2.5,
        )
        legend_entries.append(f"All Warm mu={warm_mean:.1f}, sigma={warm_std:.1f}")

    plt.xlabel("Input Noise [ENC]")
    plt.ylabel("Counts")
    plt.ylim(0, 150)
    plt.xlim(600, 1200)

    title_str = f"Module: {module_name}\nOverlaid {stream} Histograms"

    if first_timestamp:
        title_str += f"\nTimestamp: {first_timestamp}"

    plt.title(title_str)

    out_of_range_total = sum(d["low_count"] + d["high_count"] for d in low_high_summary)

    if out_of_range_total > 0:
        plt.text(
            0.98,
            0.95,
            f"Out-of-range values: {out_of_range_total} (<600 or >1100)",
            transform=plt.gca().transAxes,
            color="red",
            fontsize="small",
            ha="right",
            va="top",
        )

    plt.grid(True)

    if legend_entries:
        plt.legend(
            legend_entries,
            fontsize="x-small",
            loc="center left",
            bbox_to_anchor=(-0.02, 0.5),
        )

    plt.tight_layout()

    save_dir = os.path.join(output_base_dir, module_name, "histograms_combined_noskip")
    mkdir(save_dir)

    base = os.path.join(save_dir, f"{module_name}_combined-{stream}")

    plt.savefig(f"{base}.pdf")
    plt.savefig(f"{base}.png", dpi=300)
    plt.close()

    print(f"✅ Saved: {base}.pdf and {base}.png")

    if low_high_summary:
        csv_path = os.path.join(save_dir, f"{module_name}_{stream}_low_high_values.csv")

        with open(csv_path, mode="w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "filename",
                "stream",
                "low_count",
                "low_values",
                "high_count",
                "high_values",
            ])

            for entry in low_high_summary:
                writer.writerow([
                    entry["filename"],
                    entry["stream"],
                    entry["low_count"],
                    json.dumps(entry["low_values"]),
                    entry["high_count"],
                    json.dumps(entry["high_values"]),
                ])

        json_path = os.path.join(save_dir, f"{module_name}_{stream}_low_high_values.json")

        with open(json_path, "w") as jf:
            json.dump(low_high_summary, jf, indent=2)

        print(f"📝 Saved low/high CSV: {csv_path}")
        print(f"📝 Saved low/high JSON: {json_path}")

    return True


# ============================================================
# Error summary TXT
# ============================================================

def write_error_summary_txt(output_base_dir):
    mkdir(output_base_dir)

    summary_path = os.path.join(output_base_dir, "histograms_combined_noskip_error_summary.txt")

    categories = {
        "B": "CATEGORY B — high input noise values greater than 1100",
        "C": "CATEGORY C — low input noise values less than 600",
        "D": "CATEGORY D — files skipped, empty, missing, or unreadable",
        "E": "CATEGORY E — script did not run for entire module / no valid histogram plotted",
    }

    with open(summary_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("INPUT NOISE HISTOGRAM NOSKIP ERROR SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        total_entries = sum(len(error_summary[key]) for key in error_summary)
        f.write(f"Total issue entries found: {total_entries}\n\n")

        for category, title in categories.items():
            entries = error_summary[category]

            f.write("\n" + "=" * 80 + "\n")
            f.write(title + "\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total entries: {len(entries)}\n")

            if category in ["B", "C"]:
                total_values = sum(entry.get("count") or 0 for entry in entries)
                f.write(f"Total values: {total_values}\n")

            f.write("\n")

            if not entries:
                f.write("None\n")
                continue

            grouped = defaultdict(list)

            for entry in entries:
                grouped[entry["module"]].append(entry)

            for module, module_entries in grouped.items():
                f.write(f"\nModule: {module}\n")
                f.write("-" * 80 + "\n")

                if category in ["B", "C"]:
                    module_total = sum(entry.get("count") or 0 for entry in module_entries)
                    f.write(f"Module total values: {module_total}\n\n")

                for entry in module_entries:
                    f.write(f"File: {entry['file']}\n")
                    f.write(f"Stream: {entry.get('stream', 'N/A')}\n")

                    if category == "B":
                        f.write(f"High count: {entry.get('count', 0)}\n")
                        f.write(f"High values: {entry.get('values', [])}\n\n")

                    elif category == "C":
                        f.write(f"Low count: {entry.get('count', 0)}\n")
                        f.write(f"Low values: {entry.get('values', [])}\n\n")

                    else:
                        f.write(f"Reason: {entry['message']}\n\n")

    print("\n" + "=" * 80)
    print("Saved error summary TXT file:")
    print(summary_path)
    print("=" * 80)


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Plot combined input noise histograms"
    )

    parser.add_argument(
        "--serial_number",
        help="Serial number, e.g. 20USBHX2002592",
    )

    parser.add_argument(
        "-i",
        "--input",
        help="Glob pattern, e.g. 'UCSC/HX/SN20USBHX2002099/SN20USBHX2002099_*.json' or 'UCSC/HX/SN*/*.json'",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output base directory. Default is inferred from input path, e.g. UCSC/HX3",
    )

    args = parser.parse_args()

    if args.input:
        input_files = sorted(glob.glob(args.input))

    elif args.serial_number:
        serial = clean_serial(args.serial_number)

        input_files = sorted(
            glob.glob(f"UCSC/HX/SN{serial}/SN{serial}_*.json")
        )

        if not input_files:
            input_files = sorted(
                glob.glob(f"SN{serial}/SN{serial}_*.json")
            )

    else:
        parser.error("Please provide either --serial_number or -i/--input")

    output_base_dir = args.output or get_base_output_dir(input_files, "UCSC/HX3")

    print(f"\nFound {len(input_files)} input files")
    print(f"Output base directory: {output_base_dir}")

    if len(input_files) == 0:
        print("❌ CATEGORY E: No JSON files found.")
        add_error("E", "Unknown", None, "No JSON files found. Script did not run.")
        write_error_summary_txt(output_base_dir)
        return

    filtered_files = filter_input_files(input_files)
    grouped_files = group_files_by_module(filtered_files)

    print("\nModules:")
    for module_name, files in grouped_files.items():
        print(f"  {module_name}: {len(files)} files")

    if not grouped_files:
        print("❌ CATEGORY E: No modules found after filtering.")
        add_error("E", "Unknown", None, "No modules found after filtering.")
        write_error_summary_txt(output_base_dir)
        return

    module_plot_status = {}

    for module_name, files in grouped_files.items():
        under_ok = plot_combined_stream(
            files,
            "under",
            output_base_dir,
            module_name,
        )

        away_ok = plot_combined_stream(
            files,
            "away",
            output_base_dir,
            module_name,
        )

        module_plot_status[module_name] = under_ok or away_ok

    for module_name, ok in module_plot_status.items():
        if not ok:
            add_error(
                "E",
                module_name,
                None,
                "Script did not successfully make any histogram plot for this module.",
            )

    write_error_summary_txt(output_base_dir)


if __name__ == "__main__":
    main()