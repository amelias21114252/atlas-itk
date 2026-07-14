#!/usr/bin/env bash

# ============================================================
# run_update_website_problems_updated.sh
#
# Run with:
#   bash run_update_website_problems_updated.sh
#
# You may also source it, but running with bash is recommended:
#   source run_update_website_problems_updated.sh
#
# Full CERN-ATLAS ITk problem-category website update pipeline.
# ============================================================

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

# ------------------------------------------------------------
# Script names used by the current problem-category workflow.
# Change a value here if one of your local filenames differs.
# ------------------------------------------------------------
BNL_IV_SCRIPT="plot_multi_IV_final_BNL_Category_A_Di_warning.py"
LBNL_IV_SCRIPT="plot_multi_IV_final_LBNL_Category_A_Di_warning.py"
UCSC_IV_SCRIPT="plot_multi_IV_final_UCSC_Category_A_Di_warning.py"

BNL_INPUTNOISE_SCRIPT="plot_multi_inputnoise_BNL_one_channel_plot_trigger_10_or_more.py"
LBNL_INPUTNOISE_SCRIPT="plot_multi_inputnoise_LBNL_one_channel_subcategories.py"
UCSC_INPUTNOISE_SCRIPT="plot_multi_inputnoise_UCSC_one_channel_subcategories.py"

BNL_BC_SUMMARY_SCRIPT="generate_categoryBandC_BNL_from_inputnoise_summary.py"
LBNL_BC_SUMMARY_SCRIPT="generate_categoryBandC_LBNL_from_inputnoise_summary.py"
UCSC_BC_SUMMARY_SCRIPT="generate_categoryBandC_UCSC_from_inputnoise_summary.py"

WEBSITE_SCRIPT="get_website_displayimages_all_sites_dynamic_categories_no_hardcoded_comments.py"


print_header() {
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

run_python() {
    local script="$1"
    shift

    if [[ ! -f "$script" ]]; then
        echo "ERROR: Required script not found: $script" >&2
        exit 1
    fi

    echo "+ $PYTHON_BIN $script $*"
    "$PYTHON_BIN" "$script" "$@"
}


print_header "Starting CERN-ATLAS ITk website update pipeline"


# ============================================================
# Step 1: Check ITK_DB_AUTH token
# ============================================================

print_header "Step 1: Checking ITK_DB_AUTH token"

if [[ -z "${ITK_DB_AUTH:-}" ]]; then
    echo "ERROR: ITK_DB_AUTH is not set."
    echo ""
    echo "Run this first:"
    echo "  export ITK_DB_AUTH=YOUR_TOKEN"
    echo ""
    exit 1
fi

echo "ITK_DB_AUTH is set."


# ============================================================
# Step 2: Get latest module serial numbers
# ============================================================
# Timestamp-list scripts are no longer required by the dynamic
# website generator. Timestamps are read from the current summary
# and module-data files instead of hard-coded timestamp lists.

print_header "Step 2: Getting latest module serial numbers"

run_python "get_module_serial_numbers.py"
run_python "get_test_timestamp_full_list_BNL.py"
run_python "get_test_timestamp_full_list_LBNL.py"
run_python "get_test_timestamp_full_list_UCSC.py"


# ============================================================
# Step 3: Download ML IV JSON files
# ============================================================

print_header "Step 3: Downloading ML IV JSON files"

run_python "get_all_tests_categoryE_i_bnl.py"
run_python "get_all_tests_categoryE_i_lbnl.py"
run_python "get_all_tests_categoryE_i_ucsc.py"


# ============================================================
# Step 4: Download HX input-noise JSON files
# ============================================================

print_header "Step 4: Downloading HX input-noise JSON files"

run_python "get_all_tests_categoryDandE_ii_bnl.py" \
    --test_name "Response Curve TC" \
    --max_workers 6

run_python "get_all_tests_categoryDandE_ii_lbnl.py" \
    --test_name "Response Curve TC" \
    --max_workers 6

run_python "get_all_tests_categoryDandE_ii_ucsc.py" \
    --test_name "Response Curve TC" \
    --max_workers 6

  


# ============================================================
# Step 5: Generate IV plots and IV category summaries
# ============================================================
# These scripts generate:
#   BNL/ML/iv_error_summary.txt
#   BNL/ML/iv_category_summary_bnl.txt
#   LBNL/ML/iv_error_summary.txt
#   LBNL/ML/iv_category_summary_lbnl.txt
#   UCSC/ML/iv_error_summary.txt
#   UCSC/ML/iv_category_summary_ucsc.txt

print_header "Step 5: Generating IV plots and summaries"

run_python "$BNL_IV_SCRIPT" \
    -i "BNL/ML/*/*.json" \
    -o "BNL/ML2"

run_python "$LBNL_IV_SCRIPT" \
    -i "LBNL/ML/*/*.json" \
    -o "LBNL/ML2"

run_python "$UCSC_IV_SCRIPT" \
    -i "UCSC/ML/*/*.json" \
    -o "UCSC/ML2"


# ============================================================
# Step 6: Generate BNL input-noise problem plots
# ============================================================

print_header "Step 6: Generating BNL input-noise problem plots"

run_python "$BNL_INPUTNOISE_SCRIPT" \
    -i "BNL/HX/SN*/*.json" \
    -o "BNL/HX2"


# ============================================================
# Step 7: Generate LBNL input-noise problem plots
# ============================================================

print_header "Step 7: Generating LBNL input-noise problem plots"

run_python "$LBNL_INPUTNOISE_SCRIPT" \
    -i "LBNL/HX/SN*/*.json" \
    -o "LBNL/HX2"


# ============================================================
# Step 8: Generate UCSC input-noise problem plots
# ============================================================

print_header "Step 8: Generating UCSC input-noise problem plots"

run_python "$UCSC_INPUTNOISE_SCRIPT" \
    -i "UCSC/HX/SN*/*.json" \
    -o "UCSC/HX2"


# ============================================================
# Step 9: Generate Category B/C warning/category summaries
# ============================================================
# The input-noise plotting scripts generate inputnoise_error_summary.txt.
# These generator scripts convert those files into the final dynamic
# category-summary files consumed by the website generator.

print_header "Step 9: Generating Category B/C summaries"

run_python "$BNL_BC_SUMMARY_SCRIPT" \
    --input_file "BNL/HX2/inputnoise_error_summary_bnl.txt" \
    --output_file "BNL/HX2/inputnoise_category_summary_bnl.txt"

run_python "$LBNL_BC_SUMMARY_SCRIPT" \
    --input_file "LBNL/HX2/inputnoise_error_summary_lbnl.txt" \
    --output_file "LBNL/HX2/inputnoise_category_summary_lbnl.txt"


run_python "$UCSC_BC_SUMMARY_SCRIPT" \
    --input_file "UCSC/HX2/inputnoise_error_summary_ucsc.txt" \
    --output_file "UCSC/HX2/inputnoise_category_summary_ucsc.txt"


# ============================================================
# Step 10: Verify required dynamic summary files
# ============================================================

print_header "Step 10: Verifying dynamic category summary files"

required_summary_files=(
    "BNL/ML2/iv_category_summary_bnl.txt"
    "LBNL/ML2/iv_category_summary_lbnl.txt"
    "UCSC/ML2/iv_category_summary_ucsc.txt"
    "BNL/HX2/inputnoise_category_summary_bnl.txt"
    "LBNL/HX2/inputnoise_category_summary_lbnl.txt"
    "UCSC/HX2/inputnoise_category_summary_ucsc.txt"
)

for summary_file in "${required_summary_files[@]}"; do
    if [[ ! -s "$summary_file" ]]; then
        echo "ERROR: Required summary file is missing or empty: $summary_file" >&2
        exit 1
    fi

    echo "Verified: $summary_file"
done


# ============================================================
# Step 11: Generate final website
# ============================================================

print_header "Step 11: Generating final website"

run_python "$WEBSITE_SCRIPT"


# ============================================================
# Final message
# ============================================================

print_header "Website update complete"

echo "Generated website folder:"
echo "  categories_website/"
echo ""
echo "Expected website files:"
echo "  categories_website/index.html"
echo "  categories_website/bnl.html"
echo "  categories_website/lbnl.html"
echo "  categories_website/ucsc.html"
echo "  categories_website/bnlproblem.html"
echo "  categories_website/lbnlproblem.html"
echo "  categories_website/ucscproblem.html"
echo "  categories_website/serial_parent_map.csv"
echo "  categories_website/serial_parent_map.json"
echo ""
echo "Dynamic IV category summary files:"
echo "  BNL/ML/iv_category_summary_bnl.txt"
echo "  LBNL/ML/iv_category_summary_lbnl.txt"
echo "  UCSC/ML/iv_category_summary_ucsc.txt"
echo ""
echo "Dynamic input-noise category summary files:"
echo "  BNL/HX/inputnoise_category_summary_bnl.txt"
echo "  LBNL/HX/inputnoise_category_summary_lbnl.txt"
echo "  UCSC/HX/inputnoise_category_summary_ucsc.txt"
echo ""
echo "Problem-plot folders are generated under each site's ML and HX folders."
echo ""
echo "Upload to CERNBox / EOS:"
echo "  categories_website/"
echo "  BNL/"
echo "  LBNL/"
echo "  UCSC/"
echo ""
echo "Done."
echo "============================================================"
