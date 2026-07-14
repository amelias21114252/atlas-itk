#!/usr/bin/env python3

import json
import csv
import re
import ast
import shutil
from pathlib import Path


BASE_URL = "https://ameliame.web.cern.ch"


# ============================================================
# Output folder
# ============================================================

OUTPUT_DIR = Path("categories_website")
OUTPUT_DIR.mkdir(exist_ok=True)

institutes = {
    "BNL": [],
    "LBNL": [],
    "UCSC": [],
}

page_names = {
    "BNL": "bnl.html",
    "LBNL": "lbnl.html",
    "UCSC": "ucsc.html",
}

problem_page_names = {
    "BNL": "bnlproblem.html",
    "LBNL": "lbnlproblem.html",
    "UCSC": "ucscproblem.html",
}

NORMAL_PAGE_OUTPUT_DIRS = {
    "BNL": Path("BNL/HX3"),
    "LBNL": Path("LBNL/HX3"),
    "UCSC": Path("UCSC/HX3"),
}

PROBLEM_PAGE_OUTPUT_DIRS = {
    "BNL": Path("BNL/HX2"),
    "LBNL": Path("LBNL/HX2"),
    "UCSC": Path("UCSC/HX2"),
}

TIMESTAMP_FILES = {
    "BNL": "formatted_timestamps_bnl.txt",
    "LBNL": "formatted_timestamps_lbnl.txt",
    "UCSC": "formatted_timestamps_ucsc.txt",
}


def parse_formatted_timestamp_file(file_path):
    text = Path(file_path).read_text(encoding="utf-8")
    rows = []
    pattern = re.compile(
        r'^\s*\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)\s*,?(?:\s*#.*)?$',
        re.M,
    )

    for match in pattern.finditer(text):
        hx, ml, timestamp = [group.strip() for group in match.groups()]
        if hx or ml:
            rows.append((hx, ml, timestamp))

    if not rows:
        raise ValueError(f"No timestamp tuples found in {file_path}")

    return rows


def load_external_timestamp_lists():
    loaded = {}

    for site, filename in TIMESTAMP_FILES.items():
        candidates = [
            Path(filename),
            Path(__file__).resolve().parent / filename,
        ]

        file_path = next((candidate for candidate in candidates if candidate.exists()), None)

        if file_path is None:
            raise FileNotFoundError(
                f"Missing required timestamp file: {filename}"
            )

        loaded[site] = parse_formatted_timestamp_file(file_path)
        print(f"Loaded {site}: {len(loaded[site])} timestamps")

    institutes.clear()
    institutes.update(loaded)


load_external_timestamp_lists()


# ============================================================
# Category definitions
# ============================================================

CATEGORY_DEFINITIONS = {
    "Category A": {
        "serial_type": "ML",
        "css_class": "category-a",
        "default": "IV current above 600 nA threshold.",
        "modules": {},
    },
    "Category B(i)": {
        "serial_type": "HX",
        "css_class": "category-b",
        "default": "Away-stream input noise greater than 1100 ENC for 10 or more channels.",
        "modules": {},
    },
    "Category B(ii)": {
        "serial_type": "HX",
        "css_class": "category-b",
        "default": "Under-stream input noise greater than 1100 ENC for 10 or more channels.",
        "modules": {},
    },
    "Category C(i)": {
        "serial_type": "HX",
        "css_class": "category-c",
        "default": "Away-stream input noise less than 600 ENC for 10 or more channels.",
        "modules": {},
    },
    "Category C(ii)": {
        "serial_type": "HX",
        "css_class": "category-c",
        "default": "Under-stream input noise less than 600 ENC for 10 or more channels.",
        "modules": {},
    },
    "Category D(i)": {
        "serial_type": "ML",
        "css_class": "category-d",
        "default": "Incomplete IV dataset.",
        "modules": {},
    },
    "Category D(ii)": {
        "serial_type": "HX",
        "css_class": "category-d",
        "default": "Incomplete input-noise dataset.",
        "modules": {},
    },
    "Category E(i)": {
        "serial_type": "ML",
        "css_class": "category-e",
        "default": "IV data unavailable or could not be processed.",
        "modules": {},
    },
    "Category E(ii)": {
        "serial_type": "HX",
        "css_class": "category-e",
        "default": "Input-noise data unavailable or could not be processed.",
        "modules": {},
    },
}

ADDITIONAL_COMMENTS = {}
module_comments = {}

logo_files = {
    "BNL": "bnl.png",
    "LBNL": "lbnl.png",
    "UCSC": "scipp.png",
}


# ============================================================
# Dynamic category loaders
# ============================================================

def dynamic_normalize_serial(module):
    if not module:
        return ""

    module = str(module).strip()
    return module if module.startswith("SN") else f"SN{module}"


SITE_DYNAMIC_FILES = {
    "BNL": {
        "ml_summary": [
            "BNL/ML2/summary_page_bnl_ml.txt",
            "BNL/ML/summary_page_bnl_ml.txt",
        ],
        "iv_categories": [
            "BNL/ML2/iv_category_summary_bnl.txt",
            "BNL/ML/iv_category_summary_bnl.txt",
        ],
        "inputnoise_categories": [
            "BNL/HX2/inputnoise_category_summary_bnl.txt",
        ],
        "hx_summary": [
            "BNL/HX2/summary_page_bnl_HX.txt",
            "BNL/HX2/summary_page_bnl_hx.txt",
            "BNL/HX/summary_page_bnl_HX.txt",
            "BNL/HX/summary_page_bnl_hx.txt",
        ],
    },
    "LBNL": {
        "ml_summary": [
            "LBNL/ML2/summary_page_lbnl_ml.txt",
            "LBNL/ML/summary_page_lbnl_ml.txt",
        ],
        "iv_categories": [
            "LBNL/ML2/iv_category_summary_lbnl.txt",
            "LBNL/ML/iv_category_summary_lbnl.txt",
        ],
        "inputnoise_categories": [
            "LBNL/HX2/inputnoise_category_summary_lbnl.txt",
        ],
        "hx_summary": [
            "LBNL/HX2/summary_page_lbnl_HX.txt",
            "LBNL/HX2/summary_page_lbnl_hx.txt",
            "LBNL/HX/summary_page_lbnl_HX.txt",
            "LBNL/HX/summary_page_lbnl_hx.txt",
        ],
    },
    "UCSC": {
        "ml_summary": [
            "UCSC/ML2/summary_page_ucsc_ml.txt",
            "UCSC/ML/summary_page_ucsc_ml.txt",
        ],
        "iv_categories": [
            "UCSC/ML2/iv_category_summary_ucsc.txt",
            "UCSC/ML/iv_category_summary_ucsc.txt",
        ],
        "inputnoise_categories": [
            "UCSC/HX2/inputnoise_category_summary_ucsc.txt",
        ],
        "hx_summary": [
            "UCSC/HX2/summary_page_ucsc_HX.txt",
            "UCSC/HX2/summary_page_ucsc_hx.txt",
            "UCSC/HX/summary_page_ucsc_HX.txt",
            "UCSC/HX/summary_page_ucsc_hx.txt",
        ],
    },
}


def resolve_data_file(relative_paths, site, data_name):
    if isinstance(relative_paths, (str, Path)):
        relative_paths = [relative_paths]

    script_dir = Path(__file__).resolve().parent

    for relative_path in relative_paths:
        relative_path = Path(relative_path)
        candidates = [relative_path, script_dir / relative_path]

        for parent in (
            relative_path.parent,
            script_dir / relative_path.parent,
        ):
            if parent.exists():
                candidates.extend(
                    sorted(
                        parent.glob(
                            f"{relative_path.stem}*{relative_path.suffix}"
                        )
                    )
                )

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate

    raise FileNotFoundError(
        f"Missing required {site} {data_name} file.\n"
        f"Accepted production paths: {', '.join(map(str, relative_paths))}"
    )


def extract_python_assignment(text, variable_name, expected_type=dict):
    pattern = re.compile(
        rf"(?m)^\s*{re.escape(variable_name)}\s*=\s*"
    )
    match = pattern.search(text)

    if not match:
        return expected_type()

    start = match.end()
    opener = text[start:start + 1]
    matching = {"{": "}", "[": "]", "(": ")"}

    if opener not in matching:
        return expected_type()

    closer = matching[opener]
    depth = 0
    quote = None
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in ('"', "'"):
            quote = char
            continue

        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1

            if depth == 0:
                value = ast.literal_eval(text[start:index + 1])

                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"{variable_name} is {type(value).__name__}; "
                        f"expected {expected_type.__name__}."
                    )

                return value

    raise ValueError(f"Unterminated assignment for {variable_name}")


def normalized_comment_map(raw_map):
    normalized = {}

    for serial, comment in raw_map.items():
        serial_sn = dynamic_normalize_serial(serial)

        if serial_sn:
            normalized[serial_sn] = str(comment).strip() if comment else ""

    return normalized


def extract_serial_universe(text, serial_type):
    pattern = rf'["\'](SN)?(20USB{serial_type}\d+)["\']'

    return {
        dynamic_normalize_serial(match.group(2))
        for match in re.finditer(pattern, text)
    }


def remove_serials_from_map(mapping, serials):
    for serial in list(mapping):
        if dynamic_normalize_serial(serial) in serials:
            del mapping[serial]


def merge_additional_comment(serial, comment):
    serial = dynamic_normalize_serial(serial)

    if not serial or not comment:
        return

    current = ADDITIONAL_COMMENTS.get(serial)

    if not current:
        comments = []
    elif isinstance(current, list):
        comments = list(current)
    else:
        comments = [current]

    if comment not in comments:
        comments.append(comment)

    ADDITIONAL_COMMENTS[serial] = comments


REQUESTED_CATEGORY_DEFAULTS = {
    "Category A": "IV current above 600 nA threshold.",
    "Category B(i)": "Away-stream input noise greater than 1100 ENC for 10 or more channels.",
    "Category B(ii)": "Under-stream input noise greater than 1100 ENC for 10 or more channels.",
    "Category C(i)": "Away-stream input noise less than 600 ENC for 10 or more channels.",
    "Category C(ii)": "Under-stream input noise less than 600 ENC for 10 or more channels.",
    "Category D(i)": "Incomplete IV dataset.",
    "Category D(ii)": "Incomplete input-noise dataset.",
    "Category E(i)": "IV data unavailable or could not be processed.",
    "Category E(ii)": "Input-noise data unavailable or could not be processed.",
}


def apply_dynamic_site_categories(site):
    file_config = SITE_DYNAMIC_FILES[site]
    paths = {
        name: resolve_data_file(candidates, site, name)
        for name, candidates in file_config.items()
    }
    texts = {
        name: path.read_text(encoding="utf-8")
        for name, path in paths.items()
    }

    site_ml_serials = extract_serial_universe(texts["ml_summary"], "ML")
    site_hx_serials = extract_serial_universe(texts["hx_summary"], "HX")

    site_hx_serials |= {
        dynamic_normalize_serial(hx)
        for hx, _ml, _timestamp in institutes.get(site, [])
        if hx
    }
    site_ml_serials |= {
        dynamic_normalize_serial(ml)
        for _hx, ml, _timestamp in institutes.get(site, [])
        if ml
    }

    site_serials = site_ml_serials | site_hx_serials

    for category_data in CATEGORY_DEFINITIONS.values():
        remove_serials_from_map(category_data["modules"], site_serials)

    remove_serials_from_map(ADDITIONAL_COMMENTS, site_serials)

    iv_text = texts["iv_categories"]
    noise_text = texts["inputnoise_categories"]

    category_sources = {
        "Category A": normalized_comment_map(
            extract_python_assignment(iv_text, "category_a_comments")
        ),
        "Category B(i)": normalized_comment_map(
            extract_python_assignment(noise_text, "category_b_i_comments")
        ),
        "Category B(ii)": normalized_comment_map(
            extract_python_assignment(noise_text, "category_b_ii_comments")
        ),
        "Category C(i)": normalized_comment_map(
            extract_python_assignment(noise_text, "category_c_i_comments")
        ),
        "Category C(ii)": normalized_comment_map(
            extract_python_assignment(noise_text, "category_c_ii_comments")
        ),
        "Category D(i)": normalized_comment_map(
            extract_python_assignment(iv_text, "category_d_i_comments")
        ),
        "Category D(ii)": normalized_comment_map(
            extract_python_assignment(noise_text, "category_d_ii_comments")
        ),
        "Category E(i)": normalized_comment_map(
            extract_python_assignment(iv_text, "category_e_i_comments")
        ),
        "Category E(ii)": normalized_comment_map(
            extract_python_assignment(noise_text, "category_e_ii_comments")
        ),
    }

    category_sources["Category E(i)"].update(
        normalized_comment_map(
            extract_python_assignment(
                texts["ml_summary"],
                "category_e_i_comments",
            )
        )
    )
    category_sources["Category E(ii)"].update(
        normalized_comment_map(
            extract_python_assignment(
                texts["hx_summary"],
                "category_e_ii_comments",
            )
        )
    )
    category_sources["Category D(ii)"].update(
        normalized_comment_map(
            extract_python_assignment(
                texts["hx_summary"],
                "category_d_ii_comments",
            )
        )
    )

    for category_name, modules in category_sources.items():
        CATEGORY_DEFINITIONS[category_name]["default"] = (
            REQUESTED_CATEGORY_DEFAULTS[category_name]
        )
        CATEGORY_DEFINITIONS[category_name]["modules"].update(modules)

    warning_variable_names = (
        "yellow_warning_comments",
        "warning_b_i_comments",
        "warning_b_ii_comments",
        "warning_c_i_comments",
        "warning_c_ii_comments",
    )

    for variable_name in warning_variable_names:
        source_text = (
            iv_text
            if variable_name == "yellow_warning_comments"
            else noise_text
        )
        warning_map = normalized_comment_map(
            extract_python_assignment(source_text, variable_name)
        )

        for serial, comment in warning_map.items():
            merge_additional_comment(serial, comment)

    print(f"Loaded dynamic {site} classifications:")
    print(f"  ML serial population: {len(site_ml_serials)}")
    print(f"  HX serial population: {len(site_hx_serials)}")

    for category_name in REQUESTED_CATEGORY_DEFAULTS:
        print(
            f"  {category_name}: "
            f"{len(category_sources[category_name])}"
        )

    for name, path in paths.items():
        print(f"  {name}: {path}")


def apply_dynamic_all_sites():
    for site in ("BNL", "LBNL", "UCSC"):
        apply_dynamic_site_categories(site)


apply_dynamic_all_sites()


# ============================================================
# Status helpers
# ============================================================

status_info = {}


def normalize_serial(module):
    if not module:
        return ""

    module = str(module).strip()
    return module if module.startswith("SN") else f"SN{module}"


def strip_sn(module):
    if not module:
        return ""

    module = str(module).strip()
    return module[2:] if module.startswith("SN") else module


def get_module_message(modules, serial, default_message):
    serial_sn = normalize_serial(serial)
    serial_no_sn = strip_sn(serial)

    if serial_sn in modules:
        message = modules[serial_sn]
    elif serial_no_sn in modules:
        message = modules[serial_no_sn]
    else:
        message = default_message

    return default_message if message is None else message


def normalize_comments(value):
    if not value:
        return []

    return value if isinstance(value, list) else [value]


def build_status_info():
    status_info.clear()

    for category_name, category_data in CATEGORY_DEFINITIONS.items():
        for module in category_data["modules"]:
            serial = normalize_serial(module)

            if serial:
                status_info.setdefault(serial, []).append(category_name)


build_status_info()


# ============================================================
# URL helpers
# ============================================================

def hx_url(site, hx):
    hx = normalize_serial(hx) if hx else ""
    return f"{BASE_URL}/{site}/HX/{hx}" if hx else ""


def hx2_url(site, hx):
    hx = normalize_serial(hx) if hx else ""
    return f"{BASE_URL}/{site}/HX2/{hx}" if hx else ""


def hx3_url(site, hx):
    hx = normalize_serial(hx) if hx else ""
    return f"{BASE_URL}/{site}/HX3/{hx}" if hx else ""


def ml_url(site, ml):
    ml = normalize_serial(ml) if ml else ""
    return f"{BASE_URL}/{site}/ML/{ml}" if ml else ""


def ml2_url(site, ml):
    ml = normalize_serial(ml) if ml else ""
    return f"{BASE_URL}/{site}/ML2/{ml}" if ml else ""


def normal_page_href(site):
    return f"{BASE_URL}/{site}/HX3/{page_names[site]}"


def problem_page_href(site):
    return f"{BASE_URL}/{site}/HX2/{problem_page_names[site]}"


def home_page_href():
    return f"{BASE_URL}/categories_website/index.html"


# ============================================================
# Status formatting
# ============================================================

def get_status(hx, ml):
    notes = []

    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    if hx in status_info:
        notes.extend(status_info[hx])

    if ml in status_info:
        notes.extend(status_info[ml])

    return ("❌", "<br>".join(notes)) if notes else ("✅", "OK")


def format_status_notes(hx, ml):
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    icon, note = get_status(hx, ml)

    if icon == "✅":
        return "✅", '<div class="status-pass-box">✅ OK</div>'

    html_lines = []

    for category_name, category_data in CATEGORY_DEFINITIONS.items():
        serial = (
            ml
            if category_data["serial_type"] == "ML"
            else hx
        )

        if not serial:
            continue

        if category_name not in status_info.get(serial, []):
            continue

        message = get_module_message(
            category_data["modules"],
            serial,
            category_data["default"],
        )

        html_lines.append(
            f'<div class="status-error {category_data["css_class"]}">'
            f'❌ <strong>{category_name}:</strong> {message}'
            f'</div>'
        )

    if html_lines:
        return "❌", "\n".join(html_lines)

    return "❌", f'<div class="status-error">❌ {note}</div>'


def format_problem_status_notes(hx, ml):
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""
    html_lines = []

    for category_name, category_data in CATEGORY_DEFINITIONS.items():
        if category_name.lower().startswith("category e"):
            continue

        serial = (
            ml
            if category_data["serial_type"] == "ML"
            else hx
        )

        if not serial:
            continue

        if category_name not in status_info.get(serial, []):
            continue

        message = get_module_message(
            category_data["modules"],
            serial,
            category_data["default"],
        )

        html_lines.append(
            f'<div class="status-error {category_data["css_class"]}">'
            f'❌ <strong>{category_name}:</strong> {message}'
            f'</div>'
        )

    if html_lines:
        return "❌", "\n".join(html_lines)

    return "⚠️", '<div class="status-warning">⚠️ Additional comment only</div>'


def format_additional_comments(hx, ml):
    comments = []

    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    if hx in ADDITIONAL_COMMENTS:
        comments.extend(normalize_comments(ADDITIONAL_COMMENTS[hx]))

    if ml in ADDITIONAL_COMMENTS:
        comments.extend(normalize_comments(ADDITIONAL_COMMENTS[ml]))

    if not comments:
        return ""

    comment_lines = "".join(
        f'<div class="status-warning">⚠️ {comment}</div>'
        for comment in comments
    )

    return f"""
<div class="additional-comments-box">
  <div class="additional-comments-title">Additional comments</div>
  {comment_lines}
</div>
"""


def plot_img(src, label):
    return f"""
<div class="plot-preview">
  <div class="plot-label">{label}</div>
  <img src="{src}" alt="{label}">
</div>
"""


# ============================================================
# Navigation and shell
# ============================================================

def nav():
    return f"""
<p>
  <a href="{home_page_href()}">Home</a> |
  <a href="{normal_page_href('BNL')}">BNL</a> |
  <a href="{normal_page_href('LBNL')}">LBNL</a> |
  <a href="{normal_page_href('UCSC')}">UCSC</a> |
  <a href="{problem_page_href('BNL')}">BNL Problems</a> |
  <a href="{problem_page_href('LBNL')}">LBNL Problems</a> |
  <a href="{problem_page_href('UCSC')}">UCSC Problems</a>
</p>
"""


def category_summary():
    return """
<h2>Category Summary</h2>
<ul>
  <li><strong>Category A:</strong> IV current above 600 nA.</li>
  <li><strong>Category B(i):</strong> Away-stream input noise greater than 1100 ENC for 10 or more channels.</li>
  <li><strong>Category B(ii):</strong> Under-stream input noise greater than 1100 ENC for 10 or more channels.</li>
  <li><strong>Category C(i):</strong> Away-stream input noise less than 600 ENC for 10 or more channels.</li>
  <li><strong>Category C(ii):</strong> Under-stream input noise less than 600 ENC for 10 or more channels.</li>
  <li><strong>Category D(i):</strong> Incomplete IV dataset.</li>
  <li><strong>Category D(ii):</strong> Incomplete input-noise dataset.</li>
  <li><strong>Category E(i):</strong> IV data unavailable or could not be processed.</li>
  <li><strong>Category E(ii):</strong> Input-noise data unavailable or could not be processed.</li>
</ul>
<div class="additional-comments-legend">
  <strong>Yellow note:</strong> Additional module comments are shown when a module has useful notes that do not define a separate category.
</div>
"""


def search_controls(site, total):
    return f"""
<div class="controls">
  <input id="moduleSearch" type="text" onkeyup="filterRows()"
         placeholder="Search {site} serial, parent, status, category, timestamp, comment...">

  <select id="statusFilter" onchange="filterRows()">
    <option value="all">All statuses</option>
    <option value="pass">Pass only</option>
    <option value="category a">Category A</option>
    <option value="category b(i)">Category B(i)</option>
    <option value="category b(ii)">Category B(ii)</option>
    <option value="category c(i)">Category C(i)</option>
    <option value="category c(ii)">Category C(ii)</option>
    <option value="category d(i)">Category D(i)</option>
    <option value="category d(ii)">Category D(ii)</option>
    <option value="category e(i)">Category E(i)</option>
    <option value="category e(ii)">Category E(ii)</option>
    <option value="additional comments">Additional comments</option>
    <option value="comment">Has general comment</option>
    <option value="other">Other issues</option>
  </select>

  <div class="count-box">
    Showing <span id="visibleCount">{total}</span> of {total}
  </div>
</div>
"""


def shell(title, body):
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 2rem;
      background: #fafafa;
      color: #212529;
    }}
    h1, h2 {{ color: purple; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      background: white;
    }}
    th, td {{
      border: 1px solid #ccc;
      padding: 8px;
      vertical-align: top;
    }}
    th {{
      background: #eee;
      position: sticky;
      top: 0;
      z-index: 1;
      text-align: center;
    }}
    a {{ color: #0056b3; }}
    details > summary {{
      cursor: pointer;
      font-weight: bold;
      color: purple;
    }}
    ul {{
      margin-top: 0.25rem;
      padding-left: 1.25rem;
    }}
    .front-hero {{
      background: linear-gradient(135deg, #f4eaff, #ffffff);
      border: 1px solid #d7b7ff;
      border-radius: 22px;
      padding: 28px;
      margin-bottom: 28px;
    }}
    .front-logo-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 24px;
      margin: 28px 0;
    }}
    .front-logo-card {{
      background: white;
      border: 1px solid #d7b7ff;
      border-radius: 18px;
      padding: 24px;
      text-align: center;
    }}
    .front-logo-card img {{
      max-width: 190px;
      max-height: 115px;
      object-fit: contain;
      margin-bottom: 16px;
    }}
    .front-button {{
      display: inline-block;
      background: purple;
      color: white;
      padding: 10px 18px;
      border-radius: 12px;
      text-decoration: none;
      font-weight: bold;
    }}
    .controls {{
      display: flex;
      gap: 12px;
      align-items: center;
      margin: 20px 0;
      flex-wrap: wrap;
      background: #f4eaff;
      padding: 16px;
      border-radius: 16px;
    }}
    .controls input, .controls select {{
      font-size: 16px;
      padding: 10px 14px;
      border-radius: 12px;
      border: 1px solid #ccc;
    }}
    .controls input {{
      min-width: 360px;
      flex: 1;
    }}
    .count-box {{
      font-weight: bold;
      color: purple;
      background: white;
      padding: 10px 14px;
      border-radius: 12px;
    }}
    .status-pass {{ color: green; font-weight: bold; }}
    .status-fail {{ color: #b00020; font-weight: bold; }}
    .status-cell {{
      white-space: normal;
      min-width: 300px;
      max-width: 430px;
    }}
    .status-scroll {{
      max-height: 190px;
      overflow-y: auto;
      padding-right: 4px;
    }}
    .status-pass-box {{
      color: #1f7a3a;
      font-weight: bold;
      background: #eaf8ee;
      border: 1px solid #9bd3a8;
      border-radius: 8px;
      padding: 6px 8px;
    }}
    .status-error {{
      color: #8a0000;
      background: #ffecec;
      border: 1px solid #f3b3b3;
      border-radius: 8px;
      padding: 6px 8px;
      margin-bottom: 6px;
      font-weight: 600;
    }}
    .category-d, .category-e {{
      background: #f3eaff;
      border-color: #c9a7ff;
      color: #4b0082;
    }}
    .additional-comments-box {{
      margin-top: 8px;
      background: #fff7d6;
      border: 1px solid #ffd966;
      border-radius: 8px;
      padding: 8px;
      color: #6b4e00;
      font-weight: 600;
    }}
    .status-warning {{
      background: #fff9e6;
      border: 1px solid #ffe08a;
      border-radius: 6px;
      padding: 5px 7px;
      margin-top: 4px;
    }}
    .additional-comments-legend {{
      background: #fff7d6;
      border: 1px solid #ffd966;
      border-radius: 10px;
      padding: 10px 12px;
      margin: 12px 0 20px;
      color: #6b4e00;
    }}
    .comment-box {{
      margin-top: 8px;
      background: #f8f9fa;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 8px;
    }}
    .details-cell {{ min-width: 280px; }}
    .plot-preview {{
      margin-bottom: 14px;
      text-align: center;
    }}
    .plot-label {{
      font-weight: bold;
      margin-bottom: 5px;
    }}
    .plot-preview img {{
      width: 360px;
      max-width: 100%;
      border: 1px solid #ccc;
      background: white;
    }}
  </style>

  <script>
    function normalizeText(text) {{
      return text.toLowerCase().replace(/\\s+/g, " ").trim();
    }}

    function filterRows() {{
      const searchInput = normalizeText(
        document.getElementById("moduleSearch").value
      );
      const filterValue = document.getElementById("statusFilter").value;
      const rows = document.querySelectorAll("tbody tr.module-row");
      let visibleCount = 0;

      rows.forEach(row => {{
        const rowText = normalizeText(row.innerText);
        const categoryText = row.getAttribute("data-category") || "";
        const statusText = row.getAttribute("data-status") || "";
        const hasComment = row.getAttribute("data-comment") === "yes";
        const hasAdditional =
          row.getAttribute("data-additional-comments") === "yes";

        const matchesSearch =
          searchInput === "" || rowText.includes(searchInput);

        let matchesFilter = true;

        if (filterValue === "pass") {{
          matchesFilter = statusText === "pass";
        }} else if (filterValue === "comment") {{
          matchesFilter = hasComment;
        }} else if (filterValue === "additional comments") {{
          matchesFilter = hasAdditional;
        }} else if (filterValue !== "all") {{
          matchesFilter = categoryText.includes(filterValue);
        }}

        row.style.display =
          matchesSearch && matchesFilter ? "" : "none";

        if (matchesSearch && matchesFilter) {{
          visibleCount += 1;
        }}
      }});

      document.getElementById("visibleCount").innerText = visibleCount;
    }}

    window.addEventListener("DOMContentLoaded", filterRows);
  </script>
</head>
<body>
{nav()}
{body}
</body>
</html>
"""


# ============================================================
# Table blocks
# ============================================================

def detailed_histograms_block(hx_base, hx):
    hx = normalize_serial(hx) if hx else ""

    if not hx:
        return "No HX serial provided."

    details_html = [
        '<details><summary>View All 25 Test Runs</summary><ul>'
    ]

    for run in range(1, 26):
        run_str = f"{run:02}"

        details_html.append(
            f"""<li>
              <strong>Test Run {run_str}</strong><br>
              Combined Plots:
              <a href="{hx_base}/detailedhistograms/{hx}_{run_str}_combined_innse_away.pdf">Away</a> |
              <a href="{hx_base}/detailedhistograms/{hx}_{run_str}_combined_innse_under.pdf">Under</a>
            """
        )

        if run >= 22:
            details_html.append("<ul>")

            for channel in range(10):
                details_html.append(
                    f"""<li>
                      Channel {channel}:
                      <a href="{hx_base}/detailedhistograms/{hx}_{run_str}_innse_away_{channel}.pdf">Away</a> |
                      <a href="{hx_base}/detailedhistograms/{hx}_{run_str}_innse_under_{channel}.pdf">Under</a>
                    </li>"""
                )

            details_html.append("</ul>")

        details_html.append("</li>")

    details_html.append("</ul></details>")
    return "\n".join(details_html)


def module_row(index, site, hx, ml, timestamp):
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    hx_base = hx_url(site, hx)
    ml_base = ml_url(site, ml)
    timestamp = timestamp or "—"

    icon, note = get_status(hx, ml)
    status_class = "status-pass" if icon == "✅" else "status-fail"
    data_status = "pass" if icon == "✅" else "fail"

    _status_icon, status_html = format_status_notes(hx, ml)
    additional_comments_html = format_additional_comments(hx, ml)
    has_additional_comments = "yes" if additional_comments_html else "no"

    data_category = note.replace("<br>", " ").lower()
    if additional_comments_html:
        data_category += " additional comments"

    comment = (
        module_comments.get(hx)
        or module_comments.get(strip_sn(hx))
        or module_comments.get(ml)
        or module_comments.get(strip_sn(ml))
    )

    comment_html = (
        f'<div class="comment-box">{comment}</div>'
        if comment
        else ""
    )
    data_comment = "yes" if comment else "no"

    if hx:
        input_noise_html = f"""
<strong>Away:</strong><br>
<a href="{hx_base}/inputnoise/{hx}-away.pdf">Away</a><br>
<a href="{hx_base}/inputnoise_noskip/{hx}-away.pdf">No Skip Away</a><br><br>
<strong>Under:</strong><br>
<a href="{hx_base}/inputnoise/{hx}-under.pdf">Under</a><br>
<a href="{hx_base}/inputnoise_noskip/{hx}-under.pdf">No Skip Under</a>
"""

        combined_html = f"""
<strong>Away:</strong><br>
<a href="{hx_base}/histograms_combined/{hx}_combined-away.pdf">Away</a><br>
<a href="{hx_base}/histograms_combined_noskip/{hx}_combined-away.pdf">No Skip Away</a><br>
<a href="{hx_base}/histograms_combined_noskip/{hx}_away_low_high_values.json">JSON File</a><br><br>
<strong>Under:</strong><br>
<a href="{hx_base}/histograms_combined/{hx}_combined-under.pdf">Under</a><br>
<a href="{hx_base}/histograms_combined_noskip/{hx}_combined-under.pdf">No Skip Under</a><br>
<a href="{hx_base}/histograms_combined_noskip/{hx}_under_low_high_values.json">JSON File</a>
"""
    else:
        input_noise_html = "No HX serial provided."
        combined_html = "No HX serial provided."

    iv_html = (
        f'<a href="{ml_base}/IV/{ml}.pdf">IV Plot</a>'
        if ml
        else "No ML serial provided."
    )

    details_block = detailed_histograms_block(hx_base, hx)

    return f"""
<tr class="module-row"
    data-status="{data_status}"
    data-category="{data_category}"
    data-comment="{data_comment}"
    data-additional-comments="{has_additional_comments}">
  <td>{index}</td>
  <td>{hx or "—"}</td>
  <td>{ml or "—"}</td>
  <td>{timestamp}</td>
  <td>{input_noise_html}</td>
  <td>{iv_html}</td>
  <td>{combined_html}</td>
  <td class="details-cell">{details_block}</td>
  <td class="{status_class} status-cell">
    <div class="status-scroll">
      {status_html}
      {additional_comments_html}
      {comment_html}
    </div>
  </td>
</tr>
"""


def is_category_abcd(category_name):
    category_name = category_name.lower()

    return any(
        category_name.startswith(prefix)
        for prefix in (
            "category a",
            "category b",
            "category c",
            "category d",
        )
    )


def has_problem_or_additional_comment(hx, ml):
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    categories = (
        status_info.get(hx, [])
        + status_info.get(ml, [])
    )

    return (
        any(is_category_abcd(category) for category in categories)
        or hx in ADDITIONAL_COMMENTS
        or ml in ADDITIONAL_COMMENTS
    )


def get_problem_data_category(hx, ml, has_additional_comments):
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    categories = [
        category.lower()
        for category in (
            status_info.get(hx, [])
            + status_info.get(ml, [])
        )
        if is_category_abcd(category)
    ]

    if has_additional_comments:
        categories.append("additional comments")

    return " ".join(categories)


def problem_module_row(index, site, hx, ml, timestamp):
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    hx_base = hx_url(site, hx)
    hx2_base = hx2_url(site, hx)
    hx3_base = hx3_url(site, hx)
    ml_base = ml2_url(site, ml)
    timestamp = timestamp or "—"

    icon, _note = get_status(hx, ml)
    status_class = "status-pass" if icon == "✅" else "status-fail"
    data_status = "pass" if icon == "✅" else "fail"

    _status_icon, status_html = format_problem_status_notes(hx, ml)
    additional_comments_html = format_additional_comments(hx, ml)
    has_additional_comments = "yes" if additional_comments_html else "no"

    data_category = get_problem_data_category(
        hx,
        ml,
        bool(additional_comments_html),
    )

    comment = (
        module_comments.get(hx)
        or module_comments.get(strip_sn(hx))
        or module_comments.get(ml)
        or module_comments.get(strip_sn(ml))
    )
    comment_html = (
        f'<div class="comment-box">{comment}</div>'
        if comment
        else ""
    )
    data_comment = "yes" if comment else "no"

    if hx:
        input_noise_html = f"""
<strong>Away:</strong><br>
{plot_img(f"{hx2_base}/inputnoise/{hx}-away.png", "Away")}
{plot_img(f"{hx3_base}/inputnoise_noskip/{hx}-away.png", "No Skip Away")}
<br>
<strong>Under:</strong><br>
{plot_img(f"{hx2_base}/inputnoise/{hx}-under.png", "Under")}
{plot_img(f"{hx3_base}/inputnoise_noskip/{hx}-under.png", "No Skip Under")}
"""

        combined_html = f"""
<strong>Away:</strong><br>
{plot_img(f"{hx_base}/histograms_combined/{hx}_combined-away.png", "Away")}
{plot_img(f"{hx_base}/histograms_combined_noskip/{hx}_combined-away.png", "No Skip Away")}
<br>
<strong>Under:</strong><br>
{plot_img(f"{hx_base}/histograms_combined/{hx}_combined-under.png", "Under")}
{plot_img(f"{hx_base}/histograms_combined_noskip/{hx}_combined-under.png", "No Skip Under")}
"""
    else:
        input_noise_html = "No HX serial provided."
        combined_html = "No HX serial provided."

    iv_html = (
        plot_img(f"{ml_base}/IV/{ml}.png", "IV Plot")
        if ml
        else "No ML serial provided."
    )

    return f"""
<tr class="module-row"
    data-status="{data_status}"
    data-category="{data_category}"
    data-comment="{data_comment}"
    data-additional-comments="{has_additional_comments}">
  <td>{index}</td>
  <td>{hx or "—"}</td>
  <td>{ml or "—"}</td>
  <td>{timestamp}</td>
  <td>{input_noise_html}</td>
  <td>{iv_html}</td>
  <td>{combined_html}</td>
  <td class="{status_class} status-cell">
    <div class="status-scroll">
      {status_html}
      {additional_comments_html}
      {comment_html}
    </div>
  </td>
</tr>
"""


# ============================================================
# Page builders
# ============================================================

def build_site_page(site, pairs):
    rows = "\n".join(
        module_row(index, site, hx, ml, timestamp)
        for index, (hx, ml, timestamp) in enumerate(
            pairs,
            start=1,
        )
    )

    body = f"""
<h1>{site} Modules</h1>
{category_summary()}
<p>Total module pairs: <strong>{len(pairs)}</strong></p>
{search_controls(site, len(pairs))}
<table>
  <thead>
    <tr>
      <th>#</th>
      <th>HX Serial</th>
      <th>ML Parent</th>
      <th>Timestamp</th>
      <th>Input Noise</th>
      <th>IV Plot</th>
      <th>Combined Histograms</th>
      <th>Detailed Histograms</th>
      <th>Status / Notes</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
"""

    return shell(f"{site} Modules", body)


def build_problem_site_page(site, pairs):
    problem_pairs = [
        (hx, ml, timestamp)
        for hx, ml, timestamp in pairs
        if has_problem_or_additional_comment(hx, ml)
    ]

    rows = "\n".join(
        problem_module_row(index, site, hx, ml, timestamp)
        for index, (hx, ml, timestamp) in enumerate(
            problem_pairs,
            start=1,
        )
    )

    body = f"""
<h1>{site} Problematic Modules</h1>
{category_summary()}
<p>
  This page displays modules with Category A/B/C/D errors or
  additional comments. Modules with only Category E are not included.
</p>
<p>
  Problematic / commented module pairs:
  <strong>{len(problem_pairs)}</strong>
</p>
{search_controls(site, len(problem_pairs))}
<table>
  <thead>
    <tr>
      <th>#</th>
      <th>HX Serial</th>
      <th>ML Parent</th>
      <th>Timestamp</th>
      <th>Input Noise</th>
      <th>IV Plot</th>
      <th>Combined Histograms</th>
      <th>Status / Notes</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
"""

    return shell(f"{site} Problematic Modules", body)


def build_home_page():
    total = sum(len(pairs) for pairs in institutes.values())

    logo_cards = "\n".join(
        f"""
<div class="front-logo-card">
  <a href="{normal_page_href(site)}">
    <img src="{logo_files.get(site, '')}" alt="{site} logo">
  </a>
  <h2>{site}</h2>
  <p>{len(pairs)} module pairs</p>
  <a class="front-button" href="{normal_page_href(site)}">
    Open {site} Page
  </a>
  <br><br>
  <a class="front-button" href="{problem_page_href(site)}">
    Open {site} Problems
  </a>
</div>
"""
        for site, pairs in institutes.items()
    )

    body = f"""
<div class="front-hero">
  <h1>ATLAS ITk Strip Modules – NYU Contributions</h1>
  <p><strong>Maintained by:</strong> Amelia Stevens, CERN username: ameliame</p>
  <p>This webpage displays IV and input-noise results for silicon strip detector modules.</p>
  <p>Total module pairs: <strong>{total}</strong></p>
</div>
<h2>Institute Pages</h2>
<div class="front-logo-grid">{logo_cards}</div>
{category_summary()}
"""

    return shell("ATLAS ITk Strip Modules", body)


def copy_logo_files(out_dir):
    for site, filename in logo_files.items():
        src = Path(filename)
        dst = out_dir / filename

        if dst.exists():
            print(f"✅ Found logo already in output folder: {dst}")
        elif src.exists():
            shutil.copy(src, dst)
            print(f"✅ Copied logo: {src} -> {dst}")
        else:
            print(f"⚠️ Missing logo for {site}: expected {filename}")


# ============================================================
# Main
# ============================================================

def main():
    out_dir = OUTPUT_DIR
    out_dir.mkdir(exist_ok=True)

    copy_logo_files(out_dir)

    all_rows = []

    for site, pairs in institutes.items():
        for hx, ml, timestamp in pairs:
            hx = normalize_serial(hx) if hx else ""
            ml = normalize_serial(ml) if ml else ""

            icon, note = get_status(hx, ml)

            comment = (
                module_comments.get(hx)
                or module_comments.get(strip_sn(hx))
                or module_comments.get(ml)
                or module_comments.get(strip_sn(ml))
                or ""
            )

            additional_comments = []

            if hx in ADDITIONAL_COMMENTS:
                additional_comments.extend(
                    normalize_comments(ADDITIONAL_COMMENTS[hx])
                )

            if ml in ADDITIONAL_COMMENTS:
                additional_comments.extend(
                    normalize_comments(ADDITIONAL_COMMENTS[ml])
                )

            all_rows.append({
                "institute": site,
                "serial": hx,
                "parent": ml,
                "timestamp": timestamp,
                "status": note.replace("<br>", "; "),
                "status_icon": icon,
                "comment": comment,
                "additional_comment": "; ".join(additional_comments),
                "input_noise_away_pdf": f"{hx_url(site, hx)}/inputnoise/{hx}-away.pdf" if hx else "",
                "input_noise_under_pdf": f"{hx_url(site, hx)}/inputnoise/{hx}-under.pdf" if hx else "",
                "input_noise_noskip_away_pdf": f"{hx_url(site, hx)}/inputnoise_noskip/{hx}-away.pdf" if hx else "",
                "input_noise_noskip_under_pdf": f"{hx_url(site, hx)}/inputnoise_noskip/{hx}-under.pdf" if hx else "",
                "iv_pdf": f"{ml_url(site, ml)}/IV/{ml}.pdf" if ml else "",
                "combined_away_pdf": f"{hx_url(site, hx)}/histograms_combined/{hx}_combined-away.pdf" if hx else "",
                "combined_under_pdf": f"{hx_url(site, hx)}/histograms_combined/{hx}_combined-under.pdf" if hx else "",
                "combined_noskip_away_pdf": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_combined-away.pdf" if hx else "",
                "combined_noskip_under_pdf": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_combined-under.pdf" if hx else "",
                "input_noise_away_png": f"{hx2_url(site, hx)}/inputnoise/{hx}-away.png" if hx else "",
                "input_noise_under_png": f"{hx2_url(site, hx)}/inputnoise/{hx}-under.png" if hx else "",
                "input_noise_noskip_away_png": f"{hx3_url(site, hx)}/inputnoise_noskip/{hx}-away.png" if hx else "",
                "input_noise_noskip_under_png": f"{hx3_url(site, hx)}/inputnoise_noskip/{hx}-under.png" if hx else "",
                "combined_away_png": f"{hx_url(site, hx)}/histograms_combined/{hx}_combined-away.png" if hx else "",
                "combined_under_png": f"{hx_url(site, hx)}/histograms_combined/{hx}_combined-under.png" if hx else "",
                "combined_noskip_away_png": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_combined-away.png" if hx else "",
                "combined_noskip_under_png": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_combined-under.png" if hx else "",
                "iv_png": f"{ml2_url(site, ml)}/IV/{ml}.png" if ml else "",
                "json_away_skipped": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_away_low_high_values.json" if hx else "",
                "json_under_skipped": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_under_low_high_values.json" if hx else "",
                "detailed_histograms_base": f"{hx_url(site, hx)}/detailedhistograms" if hx else "",
            })

    with (out_dir / "serial_parent_map.json").open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(all_rows, file, indent=2)

    fieldnames = list(all_rows[0].keys()) if all_rows else []

    with (out_dir / "serial_parent_map.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    home_html = build_home_page()
    (out_dir / "index.html").write_text(
        home_html,
        encoding="utf-8",
    )

    for site, pairs in institutes.items():
        site_output_dir = NORMAL_PAGE_OUTPUT_DIRS[site]
        site_output_dir.mkdir(parents=True, exist_ok=True)

        output_path = site_output_dir / page_names[site]
        output_path.write_text(
            build_site_page(site, pairs),
            encoding="utf-8",
        )
        print(f"✅ Wrote normal page: {output_path}")

    for site, pairs in institutes.items():
        problem_output_dir = PROBLEM_PAGE_OUTPUT_DIRS[site]
        problem_output_dir.mkdir(parents=True, exist_ok=True)

        output_path = problem_output_dir / problem_page_names[site]
        output_path.write_text(
            build_problem_site_page(site, pairs),
            encoding="utf-8",
        )
        print(f"✅ Wrote problem page: {output_path}")

    with (out_dir / "index.html.json").open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump({"html": home_html}, file, indent=2)

    print(f"✅ Wrote homepage and exports to: {out_dir}/")
    print("✅ Normal institute pages:")
    print("   BNL/HX3/bnl.html")
    print("   LBNL/HX3/lbnl.html")
    print("   UCSC/HX3/ucsc.html")
    print("✅ Problem institute pages:")
    print("   BNL/HX2/bnlproblem.html")
    print("   LBNL/HX2/lbnlproblem.html")
    print("   UCSC/HX2/ucscproblem.html")


if __name__ == "__main__":
    main()
