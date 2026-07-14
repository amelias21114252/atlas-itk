#python get_website_displayimages_all_sites_dynamic_categories_no_hardcoded_comments.py

#!/usr/bin/env python3

import json
import csv
import re
from pathlib import Path
import shutil


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

TIMESTAMP_FILES = {
    "BNL": "formatted_timestamps_bnl.txt",
    "LBNL": "formatted_timestamps_lbnl.txt",
    "UCSC": "formatted_timestamps_ucsc.txt",
}

def parse_formatted_timestamp_file(file_path):
    import re
    from pathlib import Path
    text=Path(file_path).read_text(encoding="utf-8")
    rows=[]
    pat=re.compile(r'^\s*\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)\s*,?(?:\s*#.*)?$',re.M)
    for m in pat.finditer(text):
        hx,ml,ts=[g.strip() for g in m.groups()]
        if hx or ml:
            rows.append((hx,ml,ts))
    if not rows:
        raise ValueError(f"No timestamp tuples found in {file_path}")
    return rows

def load_external_timestamp_lists():
    from pathlib import Path
    loaded={}
    for site,fname in TIMESTAMP_FILES.items():
        candidates=[Path(fname),Path(__file__).resolve().parent/fname]
        fp=None
        for c in candidates:
            if c.exists():
                fp=c;break
        if fp is None:
            raise FileNotFoundError(f"Missing required timestamp file: {fname}")
        loaded[site]=parse_formatted_timestamp_file(fp)
        print(f"Loaded {site}: {len(loaded[site])} timestamps")
    institutes.clear()
    institutes.update(loaded)

load_external_timestamp_lists()


# ============================================================
# Category definitions
# One place for category lists + default messages + optional comments
#
# Format:
# "serial_without_SN": None
#     -> uses the default message
#
# "serial_without_SN": "custom comment"
#     -> uses this detailed comment
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


# ============================================================
# Additional comments / warnings
# These can apply to any category: A, B, C, D, E, or modules
# that are below an error threshold.
# These do not create categories by themselves.
# ============================================================

ADDITIONAL_COMMENTS = {}


# ============================================================
# General module comments
# Not category-specific
# ============================================================

module_comments = {}
# Required imports
# ============================================================

import json
import csv
import shutil
from pathlib import Path


# ============================================================
# Logo files for homepage
# Put these files in the same folder as this script,
# or directly inside categories_website/
# ============================================================

logo_files = {
    "BNL": "bnl.png",
    "LBNL": "lbnl.png",
    "UCSC": "scipp.png",
}


# ============================================================
# Normal page names
# ============================================================

page_names = {
    "BNL": "bnl.html",
    "LBNL": "lbnl.html",
    "UCSC": "ucsc.html",
}


# ============================================================
# Separate problematic/display page names
# ============================================================

problem_page_names = {
    "BNL": "bnlproblem.html",
    "LBNL": "lbnlproblem.html",
    "UCSC": "ucscproblem.html",
}



# ============================================================
# Dynamic category loaders for BNL, LBNL, and UCSC
#
# Timestamp behavior is intentionally unchanged. The website continues to
# read formatted_timestamps_bnl.txt, formatted_timestamps_lbnl.txt, and
# formatted_timestamps_ucsc.txt and displays each timestamp string exactly as
# stored in those tuple files.
# ============================================================

import ast


def dynamic_normalize_serial(module):
    if not module:
        return ""
    module = str(module).strip()
    return module if module.startswith("SN") else f"SN{module}"


SITE_DYNAMIC_FILES = {
    "BNL": {
        "ml_summary": [
            "BNL/ML/summary_page_bnl_ml.txt",
        ],
        "iv_categories": [
            "BNL/ML/iv_category_summary_bnl.txt",
        ],
        "inputnoise_categories": [
            "BNL/HX/inputnoise_category_summary_bnl.txt",
        ],
        "hx_summary": [
            "BNL/HX/summary_page_bnl_HX.txt",
            "BNL/HX/summary_page_bnl_hx.txt",
        ],
    },
    "LBNL": {
        "ml_summary": [
            "LBNL/ML/summary_page_lbnl_ml.txt",
        ],
        "iv_categories": [
            "LBNL/ML/iv_category_summary_lbnl.txt",
        ],
        "inputnoise_categories": [
            "LBNL/HX/inputnoise_category_summary_lbnl.txt",
        ],
        "hx_summary": [
            "LBNL/HX/summary_page_lbnl_HX.txt",
            "LBNL/HX/summary_page_lbnl_hx.txt",
        ],
    },
    "UCSC": {
        "ml_summary": [
            "UCSC/ML/summary_page_ucsc_ml.txt",
        ],
        "iv_categories": [
            "UCSC/ML/iv_category_summary_ucsc.txt",
        ],
        "inputnoise_categories": [
            "UCSC/HX/inputnoise_category_summary_ucsc.txt",
        ],
        "hx_summary": [
            "UCSC/HX/summary_page_ucsc_HX.txt",
            "UCSC/HX/summary_page_ucsc_hx.txt",
        ],
    },
}


def resolve_data_file(relative_paths, site, data_name):
    """Resolve one required summary file from accepted path variants."""
    if isinstance(relative_paths, (str, Path)):
        relative_paths = [relative_paths]

    script_dir = Path(__file__).resolve().parent
    checked = []

    for relative_path in relative_paths:
        relative_path = Path(relative_path)
        candidates = [relative_path, script_dir / relative_path]

        # Uploaded copies can have suffixes such as "(1)" or "_2".
        for parent in (relative_path.parent, script_dir / relative_path.parent):
            if parent.exists():
                candidates.extend(sorted(parent.glob(f"{relative_path.stem}*{relative_path.suffix}")))

        for candidate in candidates:
            checked.append(str(candidate))
            if candidate.exists() and candidate.is_file():
                return candidate

    raise FileNotFoundError(
        f"Missing required {site} {data_name} file.\n"
        f"Accepted production paths: {', '.join(map(str, relative_paths))}\n"
        f"Checked working-directory and script-directory locations."
    )


def extract_python_assignment(text, variable_name, expected_type=dict):
    """Safely extract a literal Python assignment from a text summary."""
    pattern = re.compile(rf"(?m)^\s*{re.escape(variable_name)}\s*=\s*")
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

    # Include every serial from the already-loaded timestamp tuples. This
    # guarantees that warning-only modules are recognized as belonging to the
    # correct institute even when a final summary page omits their serial.
    timestamp_hx_serials = {
        dynamic_normalize_serial(hx)
        for hx, _ml, _timestamp in institutes.get(site, [])
        if hx
    }
    timestamp_ml_serials = {
        dynamic_normalize_serial(ml)
        for _hx, ml, _timestamp in institutes.get(site, [])
        if ml
    }
    site_ml_serials |= timestamp_ml_serials
    site_hx_serials |= timestamp_hx_serials
    site_serials = site_ml_serials | site_hx_serials

    # Remove stale embedded entries belonging to this institute only. Entries
    # belonging to the other institutes remain until their own dynamic pass.
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

    # Final ML/HX pages are authoritative for full E populations and may also
    # contain the complete D(ii) mapping.
    category_sources["Category E(i)"].update(normalized_comment_map(
        extract_python_assignment(texts["ml_summary"], "category_e_i_comments")
    ))
    category_sources["Category E(ii)"].update(normalized_comment_map(
        extract_python_assignment(texts["hx_summary"], "category_e_ii_comments")
    ))
    category_sources["Category D(ii)"].update(normalized_comment_map(
        extract_python_assignment(texts["hx_summary"], "category_d_ii_comments")
    ))

    for category_name, modules in category_sources.items():
        CATEGORY_DEFINITIONS[category_name]["default"] = REQUESTED_CATEGORY_DEFAULTS[category_name]
        CATEGORY_DEFINITIONS[category_name]["modules"].update(modules)

    # Warnings are displayed and exported but do not replace official category
    # status. This includes IV yellow warnings and input-noise warning maps.
    warning_variable_names = (
        "yellow_warning_comments",
        "warning_b_i_comments",
        "warning_b_ii_comments",
        "warning_c_i_comments",
        "warning_c_ii_comments",
    )
    for variable_name in warning_variable_names:
        source_text = iv_text if variable_name == "yellow_warning_comments" else noise_text
        warning_map = normalized_comment_map(
            extract_python_assignment(source_text, variable_name)
        )
        for serial, comment in warning_map.items():
            merge_additional_comment(serial, comment)

    counts = {
        category: len(modules)
        for category, modules in category_sources.items()
    }
    warning_count = sum(
        1 for serial in ADDITIONAL_COMMENTS
        if dynamic_normalize_serial(serial) in site_serials
    )

    print(f"Loaded dynamic {site} classifications:")
    print(f"  ML serial population: {len(site_ml_serials)}")
    print(f"  HX serial population: {len(site_hx_serials)}")
    for category_name in REQUESTED_CATEGORY_DEFAULTS:
        print(f"  {category_name}: {counts[category_name]}")
    print(f"  Modules with additional warnings: {warning_count}")
    for name, path in paths.items():
        print(f"  {name}: {path}")


def apply_dynamic_all_sites():
    for site in ("BNL", "LBNL", "UCSC"):
        apply_dynamic_site_categories(site)

apply_dynamic_all_sites()

# ============================================================
# Build status_info automatically from CATEGORY_DEFINITIONS
# ============================================================

status_info = {}


def normalize_serial(module):
    """
    Convert both serial formats to SN format.

    20USBHX2002099    -> SN20USBHX2002099
    SN20USBHX2002099 -> SN20USBHX2002099
    """
    if not module:
        return ""

    module = str(module).strip()

    if module.startswith("SN"):
        return module

    return "SN" + module


def strip_sn(module):
    """
    Convert SN format to no-SN format.

    SN20USBHX2002099 -> 20USBHX2002099
    """
    if not module:
        return ""

    module = str(module).strip()

    if module.startswith("SN"):
        return module[2:]

    return module


def get_module_message(modules, serial, default_message):
    """
    Looks up category messages using either SN or no-SN keys.
    This fixes Category C and mixed-key dictionaries.
    """
    serial_sn = normalize_serial(serial)
    serial_no_sn = strip_sn(serial)

    if serial_sn in modules:
        message = modules[serial_sn]
    elif serial_no_sn in modules:
        message = modules[serial_no_sn]
    else:
        message = default_message

    if message is None:
        message = default_message

    return message


def normalize_comments(value):
    """
    Prevents strings from being split character-by-character.

    Works for:
        "single comment"
        ["comment 1", "comment 2"]
    """
    if not value:
        return []

    if isinstance(value, list):
        return value

    return [value]


def build_status_info():
    for category_name, category_data in CATEGORY_DEFINITIONS.items():
        for module in category_data["modules"].keys():
            serial = normalize_serial(module)

            if serial:
                status_info.setdefault(serial, []).append(category_name)


build_status_info()


# ============================================================
# URL helpers
# ============================================================

def hx_url(site, hx):
    """
    Normal HX URL.
    Used for:
      - normal institute pages
      - combined histograms on problem pages
    """
    hx = normalize_serial(hx) if hx else ""
    return f"{BASE_URL}/{site}/HX/{hx}" if hx else ""


def hx2_url(site, hx):
    """
    HX2 URL.
    Used for skipped Input Noise PNG plots on problem pages.
    """
    hx = normalize_serial(hx) if hx else ""
    return f"{BASE_URL}/{site}/HX2/{hx}" if hx else ""


def hx3_url(site, hx):
    """
    HX3 URL.
    Used for no-skip Input Noise PNG plots on problem pages.
    """
    hx = normalize_serial(hx) if hx else ""
    return f"{BASE_URL}/{site}/HX3/{hx}" if hx else ""


def ml_url(site, ml):
    ml = normalize_serial(ml) if ml else ""
    return f"{BASE_URL}/{site}/ML/{ml}" if ml else ""


# ============================================================
# Status helpers
# ============================================================

def get_status(hx, ml):
    notes = []

    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    if hx in status_info:
        notes.extend(status_info[hx])

    if ml in status_info:
        notes.extend(status_info[ml])

    if notes:
        return "❌", "<br>".join(notes)

    return "✅", "OK"


def format_status_notes(hx, ml):
    """
    Status notes for normal institute pages.
    Shows all categories, including Category E.
    """
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    icon, note = get_status(hx, ml)

    if icon == "✅":
        return "✅", '<div class="status-pass-box">✅ OK</div>'

    html_lines = []

    for category_name, category_data in CATEGORY_DEFINITIONS.items():
        serial_type = category_data["serial_type"]
        css_class = category_data["css_class"]
        default_message = category_data["default"]
        modules = category_data["modules"]

        serial = ml if serial_type == "ML" else hx

        if not serial:
            continue

        serial_sn = normalize_serial(serial)

        if serial_sn not in status_info:
            continue

        if category_name not in status_info[serial_sn]:
            continue

        message = get_module_message(modules, serial_sn, default_message)

        html_lines.append(
            f'<div class="status-error {css_class}">'
            f'❌ <strong>{category_name}:</strong> {message}'
            f'</div>'
        )

    if html_lines:
        return "❌", "\n".join(html_lines)

    return "❌", f'<div class="status-error">❌ {note}</div>'


def format_problem_status_notes(hx, ml):
    """
    Status notes for problem pages.

    Shows Category A/B/C/D.
    If the module only has additional comments, it shows that.
    Category E is not used to decide problem pages.
    """
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    html_lines = []

    for category_name, category_data in CATEGORY_DEFINITIONS.items():
        if category_name.lower().startswith("category e"):
            continue

        serial_type = category_data["serial_type"]
        css_class = category_data["css_class"]
        default_message = category_data["default"]
        modules = category_data["modules"]

        serial = ml if serial_type == "ML" else hx

        if not serial:
            continue

        serial_sn = normalize_serial(serial)

        if serial_sn not in status_info:
            continue

        if category_name not in status_info[serial_sn]:
            continue

        message = get_module_message(modules, serial_sn, default_message)

        html_lines.append(
            f'<div class="status-error {css_class}">'
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

    comment_lines = []

    for comment in comments:
        comment_lines.append(
            f'<div class="status-warning">⚠️ {comment}</div>'
        )

    return f"""
<div class="additional-comments-box">
  <div class="additional-comments-title">Additional comments</div>
  {''.join(comment_lines)}
</div>
"""


# ============================================================
# PNG image helper for separate problem/display pages
# ============================================================

def plot_img(src, label):
    """
    Display PNG image directly on webpage.
    No clickable link.
    """
    return f"""
<div class="plot-preview">
  <div class="plot-label">{label}</div>
  <img src="{src}" alt="{label}">
</div>
"""


# ============================================================
# Navigation and summary
# ============================================================

def nav():
    return """
<p>
  <a href="index.html">Home</a> |
  <a href="bnl.html">BNL</a> |
  <a href="lbnl.html">LBNL</a> |
  <a href="ucsc.html">UCSC</a> |
  <a href="bnlproblem.html">BNL Problems</a> |
  <a href="lbnlproblem.html">LBNL Problems</a> |
  <a href="ucscproblem.html">UCSC Problems</a>
</p>
"""


def category_summary():
    return """
<h2>Category Summary</h2>

<ul>
  <li><strong>Category A:</strong> IV current above threshold.</li>
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
  <input
    id="moduleSearch"
    type="text"
    onkeyup="filterRows()"
    placeholder="Search {site} serial, parent, status, category, timestamp, comment..."
  >

  <select id="statusFilter" onchange="filterRows()">
    <option value="all">All statuses</option>
    <option value="pass">Pass only</option>
    <option value="category a">Category A</option>
    <option value="category b(i)">Category B(i) — Away high input noise</option>
    <option value="category b(ii)">Category B(ii) — Under high input noise</option>
    <option value="category c(i)">Category C(i) — Away low input noise</option>
    <option value="category c(ii)">Category C(ii) — Under low input noise</option>
    <option value="category d(i)">Category D(i) — Incomplete IV dataset</option>
    <option value="category d(ii)">Category D(ii) — Incomplete input-noise dataset</option>
    <option value="category e(i)">Category E(i) — IV data unavailable</option>
    <option value="category e(ii)">Category E(ii) — Input-noise data unavailable</option>
    <option value="additional comments">Additional comments</option>
    <option value="comment">Has general comment</option>
    <option value="other">Other issues</option>
  </select>

  <div class="count-box">
    Showing <span id="visibleCount">{total}</span> of {total}
  </div>
</div>
"""


# ============================================================
# HTML shell
# ============================================================

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

    h1, h2 {{
      color: purple;
    }}

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

    a {{
      color: #0056b3;
    }}

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
      box-shadow: 0 3px 12px rgba(0, 0, 0, 0.06);
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
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
      transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}

    .front-logo-card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
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
      border: 1px solid purple;
    }}

    .front-button:hover {{
      background: #5f0080;
      color: white;
      text-decoration: none;
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
      border: 1px solid #d7b7ff;
    }}

    .controls input,
    .controls select {{
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
      border: 1px solid #d7b7ff;
    }}

    .status-pass {{
      color: green;
      font-weight: bold;
    }}

    .status-fail {{
      color: #b00020;
      font-weight: bold;
    }}

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
      line-height: 1.35;
    }}

    .category-a,
    .category-b,
    .category-c {{
      background: #ffecec;
      border-color: #f3b3b3;
      color: #8a0000;
    }}

    .category-d,
    .category-e {{
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

    .additional-comments-title {{
      font-weight: bold;
      margin-bottom: 4px;
      color: #5c4500;
    }}

    .status-warning {{
      background: #fff9e6;
      border: 1px solid #ffe08a;
      border-radius: 6px;
      padding: 5px 7px;
      margin-top: 4px;
      line-height: 1.35;
    }}

    .additional-comments-legend {{
      background: #fff7d6;
      border: 1px solid #ffd966;
      border-radius: 10px;
      padding: 10px 12px;
      margin: 12px 0 20px 0;
      color: #6b4e00;
    }}

    .comment-box {{
      margin-top: 8px;
      background: #f8f9fa;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 8px;
      color: #333;
      font-weight: normal;
    }}

    .details-cell {{
      min-width: 280px;
    }}

    .plot-preview {{
      margin-bottom: 14px;
      text-align: center;
    }}

    .plot-label {{
      font-weight: bold;
      margin-bottom: 5px;
      color: #333;
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
      const searchInput = normalizeText(document.getElementById("moduleSearch").value);
      const filterValue = document.getElementById("statusFilter").value;
      const rows = document.querySelectorAll("tbody tr.module-row");

      let visibleCount = 0;

      rows.forEach(row => {{
        const rowText = normalizeText(row.innerText);
        const categoryText = row.getAttribute("data-category") || "";
        const statusText = row.getAttribute("data-status") || "";
        const hasComment = row.getAttribute("data-comment") === "yes";
        const hasAdditionalComments = row.getAttribute("data-additional-comments") === "yes";

        const matchesSearch = searchInput === "" || rowText.includes(searchInput);

        let matchesFilter = true;

        if (filterValue === "pass") {{
          matchesFilter = statusText === "pass";
        }} else if (filterValue === "comment") {{
          matchesFilter = hasComment;
        }} else if (filterValue === "additional comments") {{
          matchesFilter = hasAdditionalComments;
        }} else if (filterValue === "other") {{
          matchesFilter =
            statusText === "fail" &&
            !categoryText.includes("category a") &&
            !categoryText.includes("category b(i)") &&
            !categoryText.includes("category b(ii)") &&
            !categoryText.includes("category c(i)") &&
            !categoryText.includes("category c(ii)") &&
            !categoryText.includes("category d(i)") &&
            !categoryText.includes("category d(ii)") &&
            !categoryText.includes("category e(i)") &&
            !categoryText.includes("category e(ii)");
        }} else if (filterValue !== "all") {{
          matchesFilter = categoryText.includes(filterValue);
        }}

        if (matchesSearch && matchesFilter) {{
          row.style.display = "";
          visibleCount += 1;
        }} else {{
          row.style.display = "none";
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
# Normal table blocks
# Normal pages keep PDF links and Detailed Histograms.
# ============================================================

def detailed_histograms_block(hx_base, hx):
    hx = normalize_serial(hx) if hx else ""

    if not hx:
        return "No HX serial provided."

    details_html = ['<details><summary>View All 25 Test Runs</summary><ul>']

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

            for ch in range(10):
                details_html.append(
                    f"""<li>
                      Channel {ch}:
                      <a href="{hx_base}/detailedhistograms/{hx}_{run_str}_innse_away_{ch}.pdf">Away</a> |
                      <a href="{hx_base}/detailedhistograms/{hx}_{run_str}_innse_under_{ch}.pdf">Under</a>
                    </li>"""
                )

            details_html.append("</ul>")

        details_html.append("</li>")

    details_html.append("</ul></details>")

    return "\n".join(details_html)


def module_row(i, site, hx, ml, timestamp):
    """
    Normal institute page row.
    Uses normal HX folder:
      {site}/HX/...
    """
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    hx_base = hx_url(site, hx)
    ml_base = ml_url(site, ml)

    timestamp = timestamp or "—"

    icon, note = get_status(hx, ml)

    status_class = "status-pass" if icon == "✅" else "status-fail"
    data_status = "pass" if icon == "✅" else "fail"

    status_icon, status_html = format_status_notes(hx, ml)

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

    comment_html = f'<div class="comment-box">{comment}</div>' if comment else ""
    data_comment = "yes" if comment else "no"

    details_block = detailed_histograms_block(hx_base, hx)

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

    iv_html = f'<a href="{ml_base}/IV/{ml}.pdf">IV Plot</a>' if ml else "No ML serial provided."

    return f"""
<tr class="module-row"
    data-status="{data_status}"
    data-category="{data_category}"
    data-comment="{data_comment}"
    data-additional-comments="{has_additional_comments}">
  <td>{i}</td>
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


# ============================================================
# Problem/display page rows
# These display PNG images and remove Detailed Histograms.
# ============================================================

def is_category_abcd(category_name):
    category_name = category_name.lower()

    return (
        category_name.startswith("category a")
        or category_name.startswith("category b")
        or category_name.startswith("category c")
        or category_name.startswith("category d")
    )


def has_problem_or_additional_comment(hx, ml):
    """
    Include in problem page if:
      - HX or ML has Category A/B/C/D, OR
      - HX or ML has an additional comment.

    Modules with only Category E are not included.
    """
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    categories = []

    if hx in status_info:
        categories.extend(status_info[hx])

    if ml in status_info:
        categories.extend(status_info[ml])

    has_category_abcd = any(
        is_category_abcd(category)
        for category in categories
    )

    has_additional_comment = (
        hx in ADDITIONAL_COMMENTS
        or ml in ADDITIONAL_COMMENTS
    )

    return has_category_abcd or has_additional_comment


def get_problem_data_category(hx, ml, has_additional_comments):
    """
    Data category for filtering problem pages.
    Removes Category E from the problem page filter data.
    """
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    categories = []

    if hx in status_info:
        categories.extend(status_info[hx])

    if ml in status_info:
        categories.extend(status_info[ml])

    categories = [
        category.lower()
        for category in categories
        if is_category_abcd(category)
    ]

    if has_additional_comments:
        categories.append("additional comments")

    return " ".join(categories)


def problem_module_row(i, site, hx, ml, timestamp):
    """
    Separate problem/display page row.

    Input Noise:
      skipped plots -> {site}/HX2/{hx}/inputnoise/
      no-skip plots -> {site}/HX3/{hx}/inputnoise_noskip/

    Combined Histograms:
      skipped plots -> {site}/HX/{hx}/histograms_combined/
      no-skip plots -> {site}/HX/{hx}/histograms_combined_noskip/

    IV:
      normal ML path -> {site}/ML/{ml}/IV/

    Displays PNG images directly.
    """
    hx = normalize_serial(hx) if hx else ""
    ml = normalize_serial(ml) if ml else ""

    hx_base = hx_url(site, hx)
    hx2_base = hx2_url(site, hx)
    hx3_base = hx3_url(site, hx)
    ml_base = ml_url(site, ml)

    timestamp = timestamp or "—"

    icon, note = get_status(hx, ml)

    status_class = "status-pass" if icon == "✅" else "status-fail"
    data_status = "pass" if icon == "✅" else "fail"

    status_icon, status_html = format_problem_status_notes(hx, ml)

    additional_comments_html = format_additional_comments(hx, ml)
    has_additional_comments = "yes" if additional_comments_html else "no"

    data_category = get_problem_data_category(
        hx,
        ml,
        additional_comments_html != ""
    )

    comment = (
        module_comments.get(hx)
        or module_comments.get(strip_sn(hx))
        or module_comments.get(ml)
        or module_comments.get(strip_sn(ml))
    )

    comment_html = f'<div class="comment-box">{comment}</div>' if comment else ""
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
        if ml else "No ML serial provided."
    )

    return f"""
<tr class="module-row"
    data-status="{data_status}"
    data-category="{data_category}"
    data-comment="{data_comment}"
    data-additional-comments="{has_additional_comments}">
  <td>{i}</td>
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
        module_row(i, site, hx, ml, timestamp)
        for i, (hx, ml, timestamp) in enumerate(pairs, start=1)
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
  <tbody>
    {rows}
  </tbody>
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
        problem_module_row(i, site, hx, ml, timestamp)
        for i, (hx, ml, timestamp) in enumerate(problem_pairs, start=1)
    )

    body = f"""
<h1>{site} Problematic Modules</h1>

{category_summary()}

<p>
  This separate page displays modules with Category A/B/C/D errors or additional comments.
  Modules with only Category E are not included.
  Plots are displayed directly as PNG images.
</p>

<p>Problematic / commented module pairs: <strong>{len(problem_pairs)}</strong></p>

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
  <tbody>
    {rows}
  </tbody>
</table>
"""

    return shell(f"{site} Problematic Modules", body)


def build_home_page():
    total = sum(len(pairs) for pairs in institutes.values())

    logo_cards = "\n".join(
        f"""
        <div class="front-logo-card">
          <a href="{page_names[site]}">
            <img src="{logo_files.get(site, '')}" alt="{site} logo">
          </a>

          <h2>{site}</h2>

          <p>{len(pairs)} module pairs</p>

          <a class="front-button" href="{page_names[site]}">
            Open {site} Page
          </a>

          <br><br>

          <a class="front-button" href="{problem_page_names[site]}">
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

<div class="front-logo-grid">
{logo_cards}
</div>

{category_summary()}
"""

    return shell("ATLAS ITk Strip Modules", body)


# ============================================================
# Copy homepage logo files
# ============================================================

def copy_logo_files(out_dir):
    """
    Copies bnl.png, lbnl.png, scipp.png into categories_website/
    if they exist in the current script directory.

    If they are already inside categories_website/, no action is needed.
    """
    for site, filename in logo_files.items():
        src = Path(filename)
        dst = out_dir / filename

        if dst.exists():
            print(f"✅ Found logo already in output folder: {dst}")
            continue

        if src.exists():
            shutil.copy(src, dst)
            print(f"✅ Copied logo: {src} -> {dst}")
        else:
            print(f"⚠️ Missing logo for {site}: expected {filename}")
            print(f"   Put it here: {dst}")


# ============================================================
# Main
# ============================================================

def main():
    load_external_timestamp_lists()

    out_dir = Path("categories_website")
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
                additional_comments.extend(normalize_comments(ADDITIONAL_COMMENTS[hx]))

            if ml in ADDITIONAL_COMMENTS:
                additional_comments.extend(normalize_comments(ADDITIONAL_COMMENTS[ml]))

            additional_comment = "; ".join(additional_comments)

            all_rows.append({
                "institute": site,
                "serial": hx,
                "parent": ml,
                "timestamp": timestamp,
                "status": note.replace("<br>", "; "),
                "status_icon": icon,
                "comment": comment,
                "additional_comment": additional_comment,

                # Original normal PDF paths
                "input_noise_away_pdf": f"{hx_url(site, hx)}/inputnoise/{hx}-away.pdf" if hx else "",
                "input_noise_under_pdf": f"{hx_url(site, hx)}/inputnoise/{hx}-under.pdf" if hx else "",
                "input_noise_noskip_away_pdf": f"{hx_url(site, hx)}/inputnoise_noskip/{hx}-away.pdf" if hx else "",
                "input_noise_noskip_under_pdf": f"{hx_url(site, hx)}/inputnoise_noskip/{hx}-under.pdf" if hx else "",
                "iv_pdf": f"{ml_url(site, ml)}/IV/{ml}.pdf" if ml else "",
                "combined_away_pdf": f"{hx_url(site, hx)}/histograms_combined/{hx}_combined-away.pdf" if hx else "",
                "combined_under_pdf": f"{hx_url(site, hx)}/histograms_combined/{hx}_combined-under.pdf" if hx else "",
                "combined_noskip_away_pdf": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_combined-away.pdf" if hx else "",
                "combined_noskip_under_pdf": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_combined-under.pdf" if hx else "",

                # Problem/display PNG paths
                # Input noise PNG uses HX2 and HX3
                "input_noise_away_png": f"{hx2_url(site, hx)}/inputnoise/{hx}-away.png" if hx else "",
                "input_noise_under_png": f"{hx2_url(site, hx)}/inputnoise/{hx}-under.png" if hx else "",
                "input_noise_noskip_away_png": f"{hx3_url(site, hx)}/inputnoise_noskip/{hx}-away.png" if hx else "",
                "input_noise_noskip_under_png": f"{hx3_url(site, hx)}/inputnoise_noskip/{hx}-under.png" if hx else "",

                # Combined histogram PNG uses normal HX, not HX2/HX3
                "combined_away_png": f"{hx_url(site, hx)}/histograms_combined/{hx}_combined-away.png" if hx else "",
                "combined_under_png": f"{hx_url(site, hx)}/histograms_combined/{hx}_combined-under.png" if hx else "",
                "combined_noskip_away_png": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_combined-away.png" if hx else "",
                "combined_noskip_under_png": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_combined-under.png" if hx else "",

                "iv_png": f"{ml_url(site, ml)}/IV/{ml}.png" if ml else "",

                "json_away_skipped": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_away_low_high_values.json" if hx else "",
                "json_under_skipped": f"{hx_url(site, hx)}/histograms_combined_noskip/{hx}_under_low_high_values.json" if hx else "",
                "detailed_histograms_base": f"{hx_url(site, hx)}/detailedhistograms" if hx else "",
            })

    with open(out_dir / "serial_parent_map.json", "w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=2)

    with open(out_dir / "serial_parent_map.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "institute",
            "serial",
            "parent",
            "timestamp",
            "status",
            "status_icon",
            "comment",
            "additional_comment",

            "input_noise_away_pdf",
            "input_noise_under_pdf",
            "input_noise_noskip_away_pdf",
            "input_noise_noskip_under_pdf",
            "iv_pdf",
            "combined_away_pdf",
            "combined_under_pdf",
            "combined_noskip_away_pdf",
            "combined_noskip_under_pdf",

            "input_noise_away_png",
            "input_noise_under_png",
            "input_noise_noskip_away_png",
            "input_noise_noskip_under_png",
            "combined_away_png",
            "combined_under_png",
            "combined_noskip_away_png",
            "combined_noskip_under_png",
            "iv_png",

            "json_away_skipped",
            "json_under_skipped",
            "detailed_histograms_base",
        ])

        for row in all_rows:
            writer.writerow([
                row["institute"],
                row["serial"],
                row["parent"],
                row["timestamp"],
                row["status"],
                row["status_icon"],
                row["comment"],
                row["additional_comment"],

                row["input_noise_away_pdf"],
                row["input_noise_under_pdf"],
                row["input_noise_noskip_away_pdf"],
                row["input_noise_noskip_under_pdf"],
                row["iv_pdf"],
                row["combined_away_pdf"],
                row["combined_under_pdf"],
                row["combined_noskip_away_pdf"],
                row["combined_noskip_under_pdf"],

                row["input_noise_away_png"],
                row["input_noise_under_png"],
                row["input_noise_noskip_away_png"],
                row["input_noise_noskip_under_png"],
                row["combined_away_png"],
                row["combined_under_png"],
                row["combined_noskip_away_png"],
                row["combined_noskip_under_png"],
                row["iv_png"],

                row["json_away_skipped"],
                row["json_under_skipped"],
                row["detailed_histograms_base"],
            ])

    home_html = build_home_page()
    (out_dir / "index.html").write_text(home_html, encoding="utf-8")

    # Write original normal institute pages
    for site, pairs in institutes.items():
        html = build_site_page(site, pairs)
        (out_dir / page_names[site]).write_text(html, encoding="utf-8")

    # Write separate problem/display pages
    for site, pairs in institutes.items():
        problem_html = build_problem_site_page(site, pairs)
        (out_dir / problem_page_names[site]).write_text(problem_html, encoding="utf-8")

    with open(out_dir / "index.html.json", "w", encoding="utf-8") as f:
        json.dump({"html": home_html}, f, indent=2)

    print(f"✅ Wrote files to: {out_dir}/")
    print("✅ Wrote serial_parent_map.json")
    print("✅ Wrote serial_parent_map.csv")
    print("✅ Wrote index.html")
    print("✅ Wrote bnl.html")
    print("✅ Wrote lbnl.html")
    print("✅ Wrote ucsc.html")
    print("✅ Wrote bnlproblem.html")
    print("✅ Wrote lbnlproblem.html")
    print("✅ Wrote ucscproblem.html")
    print("✅ Wrote index.html.json")
    print("")
    print("✅ Original pages were kept.")
    print("✅ Separate problem/display pages were created.")
    print("✅ Problem pages include Category A/B/C/D and additional comments.")
    print("✅ Modules with only Category E are not included in problem pages.")
    print("✅ Problem pages display PNG images directly.")
    print("")
    print("✅ Problem page Input Noise PNG paths:")
    print("   BNL/HX2/SN.../inputnoise/*.png")
    print("   BNL/HX3/SN.../inputnoise_noskip/*.png")
    print("   LBNL/HX2/SN.../inputnoise/*.png")
    print("   LBNL/HX3/SN.../inputnoise_noskip/*.png")
    print("   UCSC/HX2/SN.../inputnoise/*.png")
    print("   UCSC/HX3/SN.../inputnoise_noskip/*.png")
    print("")
    print("✅ Problem page Combined Histogram PNG paths:")
    print("   BNL/HX/SN.../histograms_combined/*.png")
    print("   BNL/HX/SN.../histograms_combined_noskip/*.png")
    print("   LBNL/HX/SN.../histograms_combined/*.png")
    print("   LBNL/HX/SN.../histograms_combined_noskip/*.png")
    print("   UCSC/HX/SN.../histograms_combined/*.png")
    print("   UCSC/HX/SN.../histograms_combined_noskip/*.png")
    print("")
    print("✅ Problem pages do not include Detailed Histograms column.")
    print("")
    print("Logo image files expected:")
    print(f"   {out_dir}/bnl.png")
    print(f"   {out_dir}/lbnl.png")
    print(f"   {out_dir}/scipp.png")


if __name__ == "__main__":
    main()