# ITk QC Plotting and Website Pipeline

This folder contains one complete runner and three stage scripts for downloading ITk QC data, generating problem and regular plots for BNL/LBNL/UCSC, producing category summaries, and rebuilding the website.

## Files

| File | Purpose |
|---|---|
| `run_all_itk_pipeline.sh` | Runs all stages in the correct order. This is the recommended command. |
| `01_run_data_download.sh` | Downloads or refreshes module serials, timestamps, IV JSON files, and input-noise JSON files. |
| `02_run_problem_modules_and_website.sh` | Generates problem-only IV/input-noise plots in `ML2` and `HX2`, creates Category B/C summaries, verifies summary files, and rebuilds the website. |
| `03_run_regular_modules_and_website.sh` | Generates regular IV/input-noise plots in `ML3` and `HX3`, then performs the final website rebuild. |

## Requirements

Run the scripts from the project that contains all referenced Python programs and the `BNL`, `LBNL`, and `UCSC` directories.

Required software:

- Bash
- Python 3
- Python packages required by the individual plotting and database scripts
- A valid `ITK_DB_AUTH` token when downloading fresh data

The scripts stop immediately when a command fails, a required Python script is missing, or a required summary file is missing or empty.

## Recommended one-command workflow

From the ITk project directory:

```bash
export ITK_DB_AUTH=YOUR_TOKEN
bash /path/to/itk_pipeline/run_all_itk_pipeline.sh
```

The runner uses the current working directory as the project directory. The pipeline executes:

1. Data download and refresh
2. Problem-module plotting and category summary generation
3. Regular-module plotting and final website rebuild

## Run from another directory

Use `--project-dir` when the current directory is not the ITk project directory:

```bash
export ITK_DB_AUTH=YOUR_TOKEN
bash /path/to/itk_pipeline/run_all_itk_pipeline.sh \
  --project-dir /path/to/your/itk-project
```

## Use a different Python executable

```bash
bash run_all_itk_pipeline.sh --python /path/to/venv/bin/python
```

You can also set the environment variable:

```bash
export PYTHON_BIN=/path/to/venv/bin/python
bash run_all_itk_pipeline.sh
```

## Skip downloading data

Use existing JSON data and run only plotting and website generation:

```bash
bash run_all_itk_pipeline.sh --skip-download
```

This runs Stages 2 and 3. Make sure the existing `BNL/ML`, `LBNL/ML`, `UCSC/ML`, `BNL/HX`, `LBNL/HX`, and `UCSC/HX` data are current.

## Restart at a particular stage

```bash
bash run_all_itk_pipeline.sh --start-at 2
```

Valid values are:

| Value | Starts with |
|---:|---|
| `1` | Data download |
| `2` | Problem-module plotting |
| `3` | Regular-module plotting and final website rebuild |

Examples:

```bash
# Rebuild all problem and regular outputs without downloading again
bash run_all_itk_pipeline.sh --start-at 2

# Rebuild only regular plots and the final website
bash run_all_itk_pipeline.sh --start-at 3
```

## Run each stage separately

### Stage 1: Download and refresh data

```bash
export ITK_DB_AUTH=YOUR_TOKEN
bash 01_run_data_download.sh
```

This stage runs:

- `get_module_serial_numbers.py`
- BNL/LBNL/UCSC timestamp scripts
- BNL/LBNL/UCSC IV data-download scripts
- BNL/LBNL/UCSC input-noise data-download scripts with six workers

Expected source-data locations include:

```text
BNL/ML/   LBNL/ML/   UCSC/ML/
BNL/HX/   LBNL/HX/   UCSC/HX/
```

### Stage 2: Generate problem-module outputs

```bash
bash 02_run_problem_modules_and_website.sh
```

This stage creates:

- Problem-only IV plots in `BNL/ML2`, `LBNL/ML2`, and `UCSC/ML2`
- Problem input-noise plots in `BNL/HX2`, `LBNL/HX2`, and `UCSC/HX2`
- Skip and no-skip input-noise outputs
- Combined input-noise histograms
- Detailed per-file input-noise histograms
- Category B/C summaries
- An intermediate website rebuild in `categories_website/`

The stage verifies these required files:

```text
BNL/ML2/iv_category_summary_bnl.txt
LBNL/ML2/iv_category_summary_lbnl.txt
UCSC/ML2/iv_category_summary_ucsc.txt
BNL/HX2/inputnoise_category_summary_bnl.txt
LBNL/HX2/inputnoise_category_summary_lbnl.txt
UCSC/HX2/inputnoise_category_summary_ucsc.txt
```

### Stage 3: Generate regular outputs and final website

```bash
bash 03_run_regular_modules_and_website.sh
```

This stage creates:

- Regular IV plots in `BNL/ML3`, `LBNL/ML3`, and `UCSC/ML3`
- Regular input-noise plots in `BNL/HX3`, `LBNL/HX3`, and `UCSC/HX3`
- Skip and no-skip input-noise outputs
- Combined input-noise histograms
- The final website in `categories_website/`

## Main output directories

| Directory | Contents |
|---|---|
| `BNL/ML2`, `LBNL/ML2`, `UCSC/ML2` | Problem IV plots and IV category summaries |
| `BNL/HX2`, `LBNL/HX2`, `UCSC/HX2` | Problem input-noise plots, detailed plots, JSON outputs, and B/C summaries |
| `BNL/ML3`, `LBNL/ML3`, `UCSC/ML3` | Regular IV plots |
| `BNL/HX3`, `LBNL/HX3`, `UCSC/HX3` | Regular input-noise plots |
| `categories_website/` | Generated BNL/LBNL/UCSC regular and problem website pages |

## Website generator

Stages 2 and 3 run:

```text
get_website_displayimages_existing_png_pdf_ML3_regular_ML2_problem.py
```

Stage 2 provides an intermediate website build after problem outputs. Stage 3 rebuilds the website after regular outputs and should be treated as the final build.

## Troubleshooting

### `ITK_DB_AUTH is not set`

Set the database token before running Stage 1:

```bash
export ITK_DB_AUTH=YOUR_TOKEN
```

To avoid downloading again, run:

```bash
bash run_all_itk_pipeline.sh --skip-download
```

### `Required script not found`

The project directory does not contain one of the Python programs named in the stage scripts. Run from the correct project directory or pass it explicitly:

```bash
bash run_all_itk_pipeline.sh --project-dir /correct/project/path
```

### `Required file is missing or empty`

Stage 2 expects the IV and input-noise category summary files to be produced successfully. Review the preceding Python error, confirm source JSON data exists, and rerun Stage 2.

### Run with shell command tracing

For more detailed command output:

```bash
bash -x run_all_itk_pipeline.sh --start-at 2
```

### Save a complete log

```bash
bash run_all_itk_pipeline.sh 2>&1 | tee itk_pipeline.log
```

With strict pipeline error reporting while logging:

```bash
set -o pipefail
bash run_all_itk_pipeline.sh 2>&1 | tee itk_pipeline.log
```

## Make the scripts executable

This is optional because each script can be run with `bash`, but executable permissions allow `./script.sh` usage:

```bash
chmod +x run_all_itk_pipeline.sh \
  01_run_data_download.sh \
  02_run_problem_modules_and_website.sh \
  03_run_regular_modules_and_website.sh
```

Then run:

```bash
./run_all_itk_pipeline.sh
```
