#!/usr/bin/env python3
"""
Analyze BNL input-noise JSON files and save plots only for problem
module/stream combinations.

Run:
    python plot_multi_inputnoise_BNL_one_channel_plot_trigger_10_or_more.py -i "BNL/HX/SN*/*.json" -o "BNL/HX"

Official categories use TOTAL affected channel values across all 25 tests:
    B(i)  away:  >= 10 total values above 1100 ENC
    B(ii) under: >= 10 total values above 1100 ENC
    C(i)  away:  >= 10 total values below 600 ENC
    C(ii) under: >= 10 total values below 600 ENC

Warnings:
    1-9 total affected values for the corresponding stream/category.

Plot trigger:
    Save a stream plot when there is at least one high/low affected value,
    or when Category D(ii) applies.
"""

import os
import re
import json
import shutil
import argparse
import datetime
from glob import glob
from pathlib import Path
from pprint import pprint
from collections import defaultdict, OrderedDict

import numpy as np
import matplotlib as mplt
mplt.use("Agg")
import matplotlib.pyplot as plt


# ============================================================
# Settings
# ============================================================

SITE = "BNL"
DEFAULT_OUTPUT_DIR = "BNL/HX"
EXPECTED_INPUTNOISE_TESTS = 25
KEEP_FIT_TYPE_CODE = 4

HIGH_NOISE_THRESHOLD_ENC = 1100.0
LOW_NOISE_THRESHOLD_ENC = 600.0

# Official Category B/C begins at 10 total affected values.
CATEGORY_MIN_TOTAL_VALUES = 10
CHANNEL_COUNT = 1280

RUN_TEMPERATURE = {
    1: "warm", 2: "cold", 3: "cold", 4: "warm", 5: "cold",
    6: "warm", 7: "cold", 8: "warm", 9: "cold", 10: "warm",
    11: "cold", 12: "warm", 13: "cold", 14: "warm", 15: "cold",
    16: "warm", 17: "cold", 18: "warm", 19: "cold", 20: "warm",
    21: "cold", 22: "warm", 23: "cold", 24: "cold", 25: "warm",
}

SHARED_PROBLEM_PDF_FOLDER = "category_B_C_Dii_inputnoise_plots_pdf"
PROBLEM_PARENT_FOLDER = "problem_inputnoise_plots"

CATEGORY_PDF_FOLDERS = {
    "B(i)": "Category_B_i_away_high_inputnoise",
    "B(ii)": "Category_B_ii_under_high_inputnoise",
    "C(i)": "Category_C_i_away_low_inputnoise",
    "C(ii)": "Category_C_ii_under_low_inputnoise",
    "D(ii)": "Category_D_ii_incomplete_inputnoise",
    "Warning B(i)": "Warning_B_i_away_1_to_9_high_channels",
    "Warning B(ii)": "Warning_B_ii_under_1_to_9_high_channels",
    "Warning C(i)": "Warning_C_i_away_1_to_9_low_channels",
    "Warning C(ii)": "Warning_C_ii_under_1_to_9_low_channels",
}


# ============================================================
# Helpers
# ============================================================

def flatten(input_data):
    flattened = []

    def visit(value):
        if isinstance(value, (bool, np.bool_)):
            raise TypeError("Boolean value found in input-noise data")
        if isinstance(value, (int, float, np.integer, np.floating)):
            flattened.append(float(value))
            return
        if isinstance(value, np.ndarray):
            for item in value.ravel().tolist():
                visit(item)
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                visit(item)
            return
        if isinstance(value, dict):
            for item in value.values():
                visit(item)
            return
        raise TypeError(f"Unsupported input-noise data element: {type(value)}")

    visit(input_data)
    return flattened


def json_to_dict(file_path):
    with open(file_path, "r") as infile:
        return json.load(infile)


def with_sn(serial):
    serial = str(serial or "").strip()
    if not serial:
        return ""
    return serial if serial.startswith("SN") else f"SN{serial}"


def strip_sn(serial):
    serial = str(serial or "").strip()
    return serial[2:] if serial.startswith("SN") else serial


def get_run_number(file_path):
    match = re.search(r"_(\d+)\.json$", os.path.basename(file_path))
    return int(match.group(1)) if match else None


def get_file_number(file_path):
    run = get_run_number(file_path)
    if run is not None:
        return f"{run:02}"
    return os.path.splitext(os.path.basename(file_path))[0].split("_")[-1]


def clean_parent_name(parent_name):
    if not parent_name or parent_name == "Unknown":
        return "Unknown"
    return with_sn(parent_name)


def format_timestamp(raw_timestamp):
    if not raw_timestamp:
        return "Unknown"
    return (
        str(raw_timestamp)
        .replace("T", " ")
        .split(".")[0]
        .replace("Z", "")
        .strip()
    )


def format_run_list(run_numbers):
    if not run_numbers:
        return "None"
    return ", ".join(f"{run:02}" for run in sorted(run_numbers))


def summarize_run_temperatures(run_numbers):
    labels = {
        RUN_TEMPERATURE.get(run, "unknown")
        for run in run_numbers
        if run is not None
    }
    labels.discard("unknown")
    if labels == {"warm"}:
        return "Warm-only."
    if labels == {"cold"}:
        return "Cold-only."
    if labels == {"warm", "cold"}:
        return "Warm/cold."
    return "Temperature unknown."


def normalize_fit_type_code(raw_fit_code):
    if raw_fit_code is None:
        return None
    try:
        return int(float(str(raw_fit_code).strip()))
    except (TypeError, ValueError):
        return None


def get_noise_result(results, stream):
    keys = (
        ("innse_under", "INNSE_UNDER", "inputnoise_under", "noise_under")
        if stream == "under"
        else ("innse_away", "INNSE_AWAY", "inputnoise_away", "noise_away")
    )
    for key in keys:
        if key in results:
            return results[key], key
    raise KeyError(
        f"Missing {stream}-stream input-noise data. Tried keys: {', '.join(keys)}"
    )


def stream_category_names(stream):
    return ("B(i)", "C(i)") if stream == "away" else ("B(ii)", "C(ii)")


# ============================================================
# Result storage
# ============================================================

def make_empty_result(module_name, stream):
    return {
        "module": module_name,
        "stream": stream,
        "valid_curves": [],
        "present_runs": set(),
        "valid_runs": set(),
        "missing_runs": set(),
        "invalid_runs": set(),
        "category_b_records": [],
        "category_c_records": [],
        "one_channel_high_records": [],
        "one_channel_low_records": [],
        "category_d_records": [],
        "category_e_records": [],
        "timestamp": "Unknown",
        "parent_name": "Unknown",
        "plot_saved": False,
        "plot_pdf": "",
        "shared_pdf": "",
        "category_pdf_copies": [],
        "plot_png": "",
    }


def add_record(result, key, file_path, run_number, message, **extra):
    record = {
        "module": result["module"],
        "stream": result["stream"],
        "file": os.path.basename(file_path) if file_path else "N/A",
        "run": run_number,
        "message": message,
    }
    record.update(extra)
    result[key].append(record)


# ============================================================
# Group files
# ============================================================

def inspect_and_group_input_files(input_files):
    module_files = defaultdict(list)
    unreadable_files = []

    for file_path in input_files:
        try:
            data = json_to_dict(file_path)
            module_name = (
                data.get("component")
                or data.get("serial_number")
                or data.get("properties", {}).get("det_info", {}).get("name")
                or ""
            )
            if not module_name:
                unreadable_files.append((file_path, "Could not determine module name"))
                continue
            module_files[with_sn(module_name)].append(file_path)
        except Exception as exc:
            unreadable_files.append((file_path, str(exc)))

    ordered = OrderedDict()
    for module_name in sorted(module_files):
        ordered[module_name] = sorted(
            module_files[module_name],
            key=lambda path: (
                get_run_number(path) if get_run_number(path) is not None else 999,
                os.path.basename(path),
            ),
        )
    return ordered, unreadable_files


# ============================================================
# Analysis
# ============================================================

def analyze_module_both_streams(module_name, input_files):
    stream_results = {
        "away": make_empty_result(module_name, "away"),
        "under": make_empty_result(module_name, "under"),
    }
    expected_runs = set(range(1, EXPECTED_INPUTNOISE_TESTS + 1))

    for file_path in input_files:
        basename = os.path.basename(file_path)
        run_number = get_run_number(file_path)

        for result in stream_results.values():
            if run_number is not None:
                result["present_runs"].add(run_number)

        try:
            data = json_to_dict(file_path)
            properties = data.get("properties", {})
            raw_fit_code = properties.get("fit_type_code")
            fit_code = normalize_fit_type_code(raw_fit_code)

            if raw_fit_code is not None and fit_code != KEEP_FIT_TYPE_CODE:
                message = (
                    f"{basename} — fit_type_code={raw_fit_code!r}; "
                    f"normalized={fit_code}; expected {KEEP_FIT_TYPE_CODE}"
                )
                for result in stream_results.values():
                    if run_number is not None:
                        result["invalid_runs"].add(run_number)
                    add_record(result, "category_d_records", file_path, run_number, message)
                continue

            raw_timestamp = data.get("timestamp", data.get("date"))
            parent_name = clean_parent_name(data.get("parent_name", "Unknown"))

            for result in stream_results.values():
                if result["timestamp"] == "Unknown":
                    result["timestamp"] = format_timestamp(raw_timestamp)
                if result["parent_name"] == "Unknown":
                    result["parent_name"] = parent_name

            results_dict = data.get("results", {})

            for stream in ("away", "under"):
                result = stream_results[stream]
                try:
                    noise_raw, matched_key = get_noise_result(results_dict, stream)
                    if noise_raw is None:
                        raise ValueError(f"noise data is None for key '{matched_key}'")

                    noise = np.asarray(flatten(noise_raw), dtype=float).reshape(-1)
                    if noise.size == 0:
                        raise ValueError("noise array is empty")

                    noise = noise[np.isfinite(noise)]
                    if noise.size == 0:
                        raise ValueError("noise array has no finite channel values")

                    high_count = int(np.count_nonzero(noise > HIGH_NOISE_THRESHOLD_ENC))
                    low_count = int(np.count_nonzero(noise < LOW_NOISE_THRESHOLD_ENC))
                    mean_val = float(np.mean(noise))
                    std_val = float(np.std(noise))

                    print(
                        f"CHECK {module_name} {stream} run "
                        f"{run_number if run_number is not None else '?'}: "
                        f"channels={noise.size}, >1100={high_count}, <600={low_count}, "
                        f"mean={mean_val:.1f}"
                    )

                    if high_count >= 1:
                        add_record(
                            result,
                            "one_channel_high_records",
                            file_path,
                            run_number,
                            f"{basename} — {high_count} channel value(s) above "
                            f"{HIGH_NOISE_THRESHOLD_ENC:.0f} ENC.",
                            channel_count=high_count,
                            mean=mean_val,
                        )

                    if low_count >= 1:
                        add_record(
                            result,
                            "one_channel_low_records",
                            file_path,
                            run_number,
                            f"{basename} — {low_count} channel value(s) below "
                            f"{LOW_NOISE_THRESHOLD_ENC:.0f} ENC.",
                            channel_count=low_count,
                            mean=mean_val,
                        )

                    temp = float(properties.get("DCS", {}).get("AMAC_NTCpb", 999))
                    result["valid_curves"].append({
                        "file_path": file_path,
                        "run": run_number,
                        "noise": noise,
                        "mean": mean_val,
                        "std": std_val,
                        "high_count": high_count,
                        "low_count": low_count,
                        "temperature": temp,
                    })
                    if run_number is not None:
                        result["valid_runs"].add(run_number)

                except Exception as stream_exc:
                    if run_number is not None:
                        result["invalid_runs"].add(run_number)
                    add_record(
                        result,
                        "category_d_records",
                        file_path,
                        run_number,
                        f"{basename} — {stream}-stream error: {stream_exc}",
                    )

        except Exception as file_exc:
            for stream, result in stream_results.items():
                if run_number is not None:
                    result["invalid_runs"].add(run_number)
                add_record(
                    result,
                    "category_d_records",
                    file_path,
                    run_number,
                    f"{basename} — file could not be processed for {stream} stream: {file_exc}",
                )

    # Classify by total values across all 25 tests.
    for stream, result in stream_results.items():
        b_name, c_name = stream_category_names(stream)
        total_high = sum(r.get("channel_count", 0) for r in result["one_channel_high_records"])
        total_low = sum(r.get("channel_count", 0) for r in result["one_channel_low_records"])

        if total_high >= CATEGORY_MIN_TOTAL_VALUES:
            result["category_b_records"] = []
            for source in result["one_channel_high_records"]:
                copied = dict(source)
                copied["category"] = b_name
                copied["message"] = (
                    f"{source['file']} — Category {b_name}: "
                    f"{source.get('channel_count', 0)} high value(s) in this test; "
                    f"{total_high} total values above {HIGH_NOISE_THRESHOLD_ENC:.0f} ENC "
                    f"across all tests (official threshold >= {CATEGORY_MIN_TOTAL_VALUES})."
                )
                result["category_b_records"].append(copied)

        if total_low >= CATEGORY_MIN_TOTAL_VALUES:
            result["category_c_records"] = []
            for source in result["one_channel_low_records"]:
                copied = dict(source)
                copied["category"] = c_name
                copied["message"] = (
                    f"{source['file']} — Category {c_name}: "
                    f"{source.get('channel_count', 0)} low value(s) in this test; "
                    f"{total_low} total values below {LOW_NOISE_THRESHOLD_ENC:.0f} ENC "
                    f"across all tests (official threshold >= {CATEGORY_MIN_TOTAL_VALUES})."
                )
                result["category_c_records"].append(copied)

        missing_runs = expected_runs - result["present_runs"]
        result["missing_runs"] = missing_runs
        for run_number in sorted(missing_runs):
            filename = f"{module_name}_{run_number:02}.json"
            add_record(
                result,
                "category_d_records",
                None,
                run_number,
                f"{filename} — missing",
            )
            result["category_d_records"][-1]["file"] = filename

        if not result["valid_curves"]:
            add_record(
                result,
                "category_e_records",
                None,
                None,
                f"No valid {stream}-stream input-noise curves could be processed for {module_name}.",
            )

    return stream_results


def get_result_categories(result):
    categories = []
    stream = result["stream"]

    if result["category_b_records"]:
        categories.append("B(i)" if stream == "away" else "B(ii)")
    elif result["one_channel_high_records"]:
        categories.append("Warning B(i)" if stream == "away" else "Warning B(ii)")

    if result["category_c_records"]:
        categories.append("C(i)" if stream == "away" else "C(ii)")
    elif result["one_channel_low_records"]:
        categories.append("Warning C(i)" if stream == "away" else "Warning C(ii)")

    if result["category_d_records"]:
        categories.append("D(ii)")

    return categories


def is_problem_result(result):
    return bool(
        result["one_channel_high_records"]
        or result["one_channel_low_records"]
        or result["category_d_records"]
    )


# ============================================================
# Plotting
# ============================================================

def plot_problem_module_stream(result, output_base_dir, save_png=True):
    module_name = result["module"]
    stream = result["stream"]

    if not is_problem_result(result):
        return False
    if not result["valid_curves"]:
        print(f"Cannot plot {module_name}, stream={stream}: no valid curves")
        return False

    fig, ax = plt.subplots(figsize=(16, 9))
    curves = sorted(
        result["valid_curves"],
        key=lambda curve: (
            curve["run"] if curve["run"] is not None else 999,
            os.path.basename(curve["file_path"]),
        ),
    )

    n_curves = max(len(curves), 1)
    blues = mplt.cm.Blues(np.linspace(0.4, 0.9, n_curves))
    oranges = mplt.cm.Oranges(np.linspace(0.4, 0.9, n_curves))

    for idx, curve in enumerate(curves):
        temp = curve["temperature"]
        temp_label = "+20C" if temp > 10 else "-35C"
        color = oranges[idx] if temp > 10 else blues[idx]
        file_number = (
            f"{curve['run']:02}" if curve["run"] is not None
            else get_file_number(curve["file_path"])
        )
        ax.plot(
            range(len(curve["noise"])),
            curve["noise"],
            lw=1,
            ls="-",
            c=color,
            label=f"{temp_label} file {file_number} [mu: {curve['mean']:.1f}]",
        )

    ax.set_xlim(0, CHANNEL_COUNT)
    ax.set_ylim(0, 2000)
    ax.set_xlabel("Channel number", labelpad=15, fontsize=38)
    ax.set_ylabel("Input noise [ENC]", labelpad=15, fontsize=38)
    ax.tick_params(axis="both", labelsize=28)
    ax.set_xticks(list(range(0, CHANNEL_COUNT + 1, 128)))

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(
            handles,
            labels,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.995),
            ncol=4,
            prop={"size": 14},
            frameon=False,
        )

    fig.text(0.15, 0.31, r"3 point gain response curve, $-$350V, times UTC", size=22)
    fig.text(0.15, 0.27, f"{module_name}, Stream: {stream}", size=28)
    fig.text(0.15, 0.23, f"Parent Module: {result['parent_name']}", size=22)
    fig.text(0.15, 0.19, f"Timestamp: {result['timestamp']}", size=22)

    plt.tight_layout(pad=0.3)
    plt.subplots_adjust(top=0.88, bottom=0.12, left=0.11, right=0.97)

    normal_dir = Path(output_base_dir) / module_name / "inputnoise"
    shared_dir = Path(output_base_dir) / SHARED_PROBLEM_PDF_FOLDER
    normal_dir.mkdir(parents=True, exist_ok=True)
    shared_dir.mkdir(parents=True, exist_ok=True)

    normal_pdf = normal_dir / f"{module_name}-{stream}.pdf"
    normal_png = normal_dir / f"{module_name}-{stream}.png"
    shared_pdf = shared_dir / f"{module_name}-{stream}.pdf"

    plt.savefig(normal_pdf, format="pdf")
    shutil.copy2(normal_pdf, shared_pdf)

    copies = []
    for category_name in get_result_categories(result):
        category_dir = (
            Path(output_base_dir)
            / PROBLEM_PARENT_FOLDER
            / CATEGORY_PDF_FOLDERS[category_name]
        )
        category_dir.mkdir(parents=True, exist_ok=True)
        category_pdf = category_dir / f"{module_name}-{stream}.pdf"
        shutil.copy2(normal_pdf, category_pdf)
        copies.append(str(category_pdf))

    if save_png:
        plt.savefig(normal_png, format="png", dpi=200)

    plt.close(fig)

    result["plot_saved"] = True
    result["plot_pdf"] = str(normal_pdf)
    result["shared_pdf"] = str(shared_pdf)
    result["category_pdf_copies"] = copies
    result["plot_png"] = str(normal_png) if save_png else ""
    return True


# ============================================================
# Summaries
# ============================================================

def group_records(results, key):
    records = []
    for result in results:
        records.extend(result[key])
    return records


def write_record_section(outfile, title, records):
    outfile.write("\n" + "=" * 80 + "\n")
    outfile.write(title + "\n")
    outfile.write("=" * 80 + "\n")
    outfile.write(f"Total records: {len(records)}\n\n")

    grouped = defaultdict(list)
    for record in records:
        grouped[(record["module"], record["stream"])].append(record)

    if not grouped:
        outfile.write("None\n")
        return

    for module_name, stream in sorted(grouped):
        outfile.write(f"\nModule: {module_name}\nStream: {stream}\n")
        outfile.write("-" * 80 + "\n")
        for record in grouped[(module_name, stream)]:
            outfile.write(f"File: {record['file']}\n")
            outfile.write(f"Reason: {record['message']}\n\n")


def build_module_comments(results):
    comments = {
        "B(i)": OrderedDict(), "B(ii)": OrderedDict(),
        "C(i)": OrderedDict(), "C(ii)": OrderedDict(),
        "D(ii)": OrderedDict(), "E(ii)": OrderedDict(),
    }

    for result in sorted(results, key=lambda x: (x["module"], x["stream"])):
        module = result["module"]
        stream = result["stream"]
        b_name, c_name = stream_category_names(stream)

        if result["category_b_records"]:
            runs = {r["run"] for r in result["one_channel_high_records"] if r["run"] is not None}
            total = sum(r.get("channel_count", 0) for r in result["one_channel_high_records"])
            rate = 100.0 * len(runs) / EXPECTED_INPUTNOISE_TESTS
            comments[b_name][module] = (
                f"{stream} stream: {total} high values greater than "
                f"{HIGH_NOISE_THRESHOLD_ENC:.0f} ENC in "
                f"{len(runs)}/{EXPECTED_INPUTNOISE_TESTS} tests. "
                f"Error rate: {rate:.2f}%. {summarize_run_temperatures(runs)} "
                f"Affected runs: {format_run_list(runs)}."
            )

        if result["category_c_records"]:
            runs = {r["run"] for r in result["one_channel_low_records"] if r["run"] is not None}
            total = sum(r.get("channel_count", 0) for r in result["one_channel_low_records"])
            rate = 100.0 * len(runs) / EXPECTED_INPUTNOISE_TESTS
            comments[c_name][module] = (
                f"{stream} stream: {total} low values less than "
                f"{LOW_NOISE_THRESHOLD_ENC:.0f} ENC in "
                f"{len(runs)}/{EXPECTED_INPUTNOISE_TESTS} tests. "
                f"Error rate: {rate:.2f}%. {summarize_run_temperatures(runs)} "
                f"Affected runs: {format_run_list(runs)}."
            )

        if result["category_d_records"]:
            runs = {r["run"] for r in result["category_d_records"] if r["run"] is not None}
            comments["D(ii)"].setdefault(module, []).append(
                f"{stream.capitalize()} stream: {len(result['valid_runs'])}/"
                f"{EXPECTED_INPUTNOISE_TESTS} tests processed successfully; "
                f"incomplete/invalid runs: {format_run_list(runs)}."
            )

        if result["category_e_records"]:
            comments["E(ii)"].setdefault(module, []).append(
                result["category_e_records"][0]["message"]
            )

    for category in ("D(ii)", "E(ii)"):
        comments[category] = OrderedDict(
            (module, " ".join(parts))
            for module, parts in comments[category].items()
        )
    return comments


def write_error_summary_txt(results, output_dir, unreadable_files):
    output_dir = Path(output_dir)
    summary_path = output_dir / "inputnoise_error_summary.txt"

    with summary_path.open("w") as outfile:
        outfile.write("=" * 80 + "\nBNL INPUT NOISE ERROR SUMMARY\n" + "=" * 80 + "\n\n")
        outfile.write(f"Generated: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n")
        outfile.write(
            f"Official high category: >= {CATEGORY_MIN_TOTAL_VALUES} total values "
            f"> {HIGH_NOISE_THRESHOLD_ENC:.0f} ENC across all tests\n"
        )
        outfile.write(
            f"Official low category: >= {CATEGORY_MIN_TOTAL_VALUES} total values "
            f"< {LOW_NOISE_THRESHOLD_ENC:.0f} ENC across all tests\n"
        )
        outfile.write("Warning range: 1-9 total affected values\n")
        outfile.write(f"Expected tests per module: {EXPECTED_INPUTNOISE_TESTS}\n\n")

        write_record_section(outfile, "CATEGORY B(i) / B(ii)", group_records(results, "category_b_records"))
        write_record_section(outfile, "CATEGORY C(i) / C(ii)", group_records(results, "category_c_records"))
        write_record_section(outfile, "ONE-CHANNEL HIGH WARNINGS", group_records(results, "one_channel_high_records"))
        write_record_section(outfile, "ONE-CHANNEL LOW WARNINGS", group_records(results, "one_channel_low_records"))
        write_record_section(outfile, "CATEGORY D(ii)", group_records(results, "category_d_records"))
        write_record_section(outfile, "CATEGORY E(ii)", group_records(results, "category_e_records"))

        if unreadable_files:
            outfile.write("\nUNREADABLE / UNASSIGNED FILES\n" + "-" * 80 + "\n")
            for file_path, reason in unreadable_files:
                outfile.write(f"File: {file_path}\nReason: {reason}\n\n")

    print(f"Saved input-noise error summary: {summary_path}")
    return summary_path


def write_comment_dict(outfile, variable_name, comments):
    outfile.write(f"{variable_name} = {{\n")
    for module, comment in comments.items():
        outfile.write(f'    "{module}": "{comment}",\n')
    outfile.write("}\n\n")


def write_modules_format(outfile, comments):
    outfile.write('"modules": {\n')
    for module, comment in comments.items():
        outfile.write(f'    "{strip_sn(module)}": "{comment}",\n')
    outfile.write("}\n\n")


def write_category_summary_txt(results, output_dir):
    output_dir = Path(output_dir)
    summary_path = output_dir / "inputnoise_category_summary_bnl.txt"
    comments = build_module_comments(results)

    with summary_path.open("w") as outfile:
        outfile.write("=" * 80 + "\nBNL INPUT NOISE CATEGORY SUMMARY\n" + "=" * 80 + "\n\n")
        outfile.write(
            f"Official Category B/C threshold: {CATEGORY_MIN_TOTAL_VALUES} or more "
            "total affected channel values across all 25 tests for one stream.\n"
        )
        outfile.write("Warning threshold: 1-9 total affected channel values.\n\n")

        variable_names = {
            "B(i)": "category_b_i_comments",
            "B(ii)": "category_b_ii_comments",
            "C(i)": "category_c_i_comments",
            "C(ii)": "category_c_ii_comments",
            "D(ii)": "category_d_ii_comments",
            "E(ii)": "category_e_ii_comments",
        }

        for category, category_comments in comments.items():
            outfile.write("=" * 80 + f"\nCATEGORY {category} COMMENTS\n" + "=" * 80 + "\n\n")
            write_comment_dict(outfile, variable_names[category], category_comments)
            write_modules_format(outfile, category_comments)

    print(f"Saved input-noise category summary: {summary_path}")
    return summary_path


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analyze BNL input-noise streams using >=10 total-value categories."
    )
    parser.add_argument("--serial_number")
    parser.add_argument("-i", "--input")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--no_png", action="store_true")
    args = parser.parse_args()

    if args.input:
        input_files = sorted(glob(args.input))
    elif args.serial_number:
        serial = strip_sn(args.serial_number)
        input_files = sorted(glob(f"{args.output}/SN{serial}/SN{serial}_*.json"))
    else:
        parser.error("Provide either --serial_number or -i/--input")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    for folder in CATEGORY_PDF_FOLDERS.values():
        (output_dir / PROBLEM_PARENT_FOLDER / folder).mkdir(parents=True, exist_ok=True)

    print(f"Found {len(input_files)} input files")
    if not input_files:
        raise FileNotFoundError("No JSON files found")

    pprint(input_files)
    module_file_map, unreadable_files = inspect_and_group_input_files(input_files)
    results = []

    for module_name, module_files in module_file_map.items():
        stream_results = analyze_module_both_streams(module_name, module_files)
        for stream in ("away", "under"):
            result = stream_results[stream]
            if is_problem_result(result):
                plot_problem_module_stream(result, output_dir, save_png=not args.no_png)
            results.append(result)

    results.sort(key=lambda item: (item["module"], item["stream"]))
    error_path = write_error_summary_txt(results, output_dir, unreadable_files)
    category_path = write_category_summary_txt(results, output_dir)

    print("\nDONE")
    print(f"Modules analyzed: {len(module_file_map)}")
    print(f"Plots saved: {sum(1 for r in results if r['plot_saved'])}")
    print(f"Saved: {error_path}")
    print(f"Saved: {category_path}")


if __name__ == "__main__":
    main()
