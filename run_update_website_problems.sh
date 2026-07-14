#!/bin/bash

# ============================================================
# run_update_website_problems.sh
#
# Run with:
#   source run_update_website_problems.sh
#
# or:
#   bash run_update_website_problems.sh
#
# Full CERN-ATLAS ITk website update pipeline.
# ============================================================
set -e

echo "============================================================"
echo "Starting CERN-ATLAS ITk website update pipeline"
echo "============================================================"


# ============================================================
# Step 1: Check ITK_DB_AUTH token
# ============================================================

echo ""
echo "Step 1: Checking ITK_DB_AUTH token"

if [ -z "$ITK_DB_AUTH" ]; then
    echo "ERROR: ITK_DB_AUTH is not set."
    echo ""
    echo "Run this first:"
    echo "export ITK_DB_AUTH=YOUR_TOKEN"
    echo ""
    exit 1
fi

echo "ITK_DB_AUTH is set."

============================================================
Step 2: Get latest module serial numbers
============================================================

echo ""
echo "Step 2: Getting latest module serial numbers"

python get_module_serial_numbers.py
python get_test_timestamp_full_list_BNL.py
python get_test_timestamp_full_list_LBNL.py
python get_test_timestamp_full_list_UCSC.py

# ============================================================
# Step 3: Download ML IV JSON files
# ============================================================

echo ""
echo "Step 3: Downloading ML IV JSON files"
python get_all_tests_categoryE_i_bnl.py
python get_all_tests_categoryE_i_lbnl.py
python get_all_tests_categoryE_i_ucsc.py

# ============================================================
# Step 4: Download HX input-noise JSON files
# ============================================================
echo ""
echo "Step 4: Downloading HX input-noise JSON files"
python get_all_tests_categoryDandE_ii_bnl.py --test_name "Response Curve TC" --max_workers 6
python get_all_tests_categoryDandE_ii_lbnl.py --test_name "Response Curve TC" --max_workers 6
python get_all_tests_categoryDandE_ii_ucsc.py --test_name "Response Curve TC" --max_workers 6

# ============================================================
# Step 5: Generate IV plots
# ============================================================

echo ""
echo "Step 5: Generating IV plots"

python plot_multi_IV_final_BNL_Category_A_Di_warning.py -i "BNL/ML/*/*.json"
python plot_multi_IV_final_LBNL_Category_A_Di_warning.py -i "LBNL/ML/*/*.json"
python plot_multi_IV_final_UCSC_Category_A_Di_warning.py -i "UCSC/ML/*/*.json"
# python plot_multi_IV_final_BNL.py -i "BNL/ML/*/*.json"
# python plot_multi_IV_final_LBNL.py -i "LBNL/ML/*/*.json"
# python plot_multi_IV_final_UCSC.py -i "UCSC/ML/*/*.json"

# ============================================================
# Step 6: Generate BNL input-noise plots
# ============================================================

echo ""
echo "Step 6: Generating BNL input-noise plots"


# python plot_multi_inputnoise_BNL.py -i "BNL/HX/SN*/*.json"
# python plot_multi_inputnoise_noskip_BNL.py -i "BNL/HX/SN*/*.json"
# python plot_combined_inputnoise_BNL.py -i "BNL/HX/SN*/*.json"
# python plot_combined_inputnoise_noskip_BNL.py -i "BNL/HX/SN*/*.json"
# python plot_detailed_inputnoise_histograms_per_file_BNL.py -i "BNL/HX/SN*/*.json"


# ============================================================
# Step 7: Generate LBNL input-noise plots
# ============================================================

echo ""
echo "Step 7: Generating LBNL input-noise plots"


# python plot_multi_inputnoise_LBNL.py -i "LBNL/HX/SN*/*.json"
# python plot_multi_inputnoise_noskip_LBNL.py -i "LBNL/HX/SN*/*.json"
# python plot_combined_inputnoise_LBNL.py -i "LBNL/HX/SN*/*.json"
# python plot_combined_inputnoise_noskip_LBNL.py -i "LBNL/HX/SN*/*.json"
# python plot_detailed_inputnoise_histograms_per_file_LBNL.py -i "LBNL/HX/SN*/*.json"


# ============================================================
# Step 8: Generate UCSC input-noise plots
# ============================================================

echo ""
echo "Step 8: Generating UCSC input-noise plots"


# python plot_multi_inputnoise_UCSC.py -i "UCSC/HX/SN*/*.json"
# python plot_multi_inputnoise_noskip_UCSC.py -i "UCSC/HX/SN*/*.json"
# python plot_combined_inputnoise_UCSC.py -i "UCSC/HX/SN*/*.json"
# python plot_combined_inputnoise_noskip_UCSC.py -i "UCSC/HX/SN*/*.json"
# python plot_detailed_inputnoise_histograms_per_file_UCSC.py -i "UCSC/HX/SN*/*.json"


# ============================================================
# Step 9: Generate combined Category A/D summaries
# ============================================================

# echo ""
# echo "Step 9: Generating combined Category A/D summaries"

# python generate_categoryAandD_BNL.py \
#   --input_file BNL/ML/iv_error_summary.txt \
#   --output_file BNL/ML/categoryAandD_summary_bnl.txt

# python generate_categoryAandD_LBNL.py \
#   --input_file LBNL/ML/iv_error_summary.txt \
#   --output_file LBNL/ML/categoryAandD_summary_lbnl.txt

# python generate_categoryAandD_UCSC.py \
#   --input_file UCSC/ML/iv_error_summary.txt \
#   --output_file UCSC/ML/categoryAandD_summary_ucsc.txt


# ============================================================
# Step 10: Generate combined Category B/C summaries
# ============================================================

echo ""
echo "Step 10: Generating combined Category B/C summaries"


python generate_categoryBandC_BNL_from_inputnoise_summary.py
python generate_categoryBandC_LBNL_from_inputnoise_summary.py
python generate_categoryBandC_UCSC_from_inputnoise_summary.py

# python generate_categoryBandC_BNL.py \
#   --input_file BNL/HX/histograms_combined_error_summary.txt \
#   --output_file BNL/HX/categoryBandC_summary_bnl.txt

# python generate_categoryBandC_LBNL.py \
#   --input_file LBNL/HX/histograms_combined_error_summary.txt \
#   --output_file LBNL/HX/categoryBandC_summary_lbnl.txt

# python generate_categoryBandC_UCSC.py \
#   --input_file UCSC/HX/histograms_combined_error_summary.txt \
#   --output_file UCSC/HX/categoryBandC_summary_ucsc.txt

# ============================================================
# Step 11: Generate final website
# ============================================================

echo ""
echo "Step 11: Generating final website"

python get_website_displayimages_all_sites_dynamic_categories_no_hardcoded_comments.py


# ============================================================
# Final message
# ============================================================

echo ""
echo "============================================================"
echo "Website update complete."
echo "============================================================"
echo ""
echo "Generated website folder:"
echo "  categories_website/"
echo ""
echo "Files created:"
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
echo "Category summary files created:"
echo "  BNL/ML/categoryAandD_summary_bnl.txt"
echo "  LBNL/ML/categoryAandD_summary_lbnl.txt"
echo "  UCSC/ML/categoryAandD_summary_ucsc.txt"
echo "  BNL/HX/categoryBandC_summary_bnl.txt"
echo "  LBNL/HX/categoryBandC_summary_lbnl.txt"
echo "  UCSC/HX/categoryBandC_summary_ucsc.txt"
echo ""
echo "Upload these to CERNBox / EOS:"
echo "  categories_website/index.html"
echo "  categories_website/bnl.html"
echo "  categories_website/lbnl.html"
echo "  categories_website/ucsc.html"
echo "  categories_website/bnlproblem.html"
echo "  categories_website/lbnlproblem.html"
echo "  categories_website/ucscproblem.html"
echo "  BNL/"
echo "  LBNL/"
echo "  UCSC/"
echo ""
echo "Done."
echo "============================================================"