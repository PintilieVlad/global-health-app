"""Import pipeline (ETL): the only part of the app that calls external sources or
writes to the database.

extract_*.py    download and save the raw responses in data/raw/<source>/
transform_*.py  turn a saved file into the normalized observation table
clean.py        cleaning rules and the IQR outlier flag
load.py         upserts and import_log
import_*.py     one import script per source; each declares its source and indicators
import_runner.py  the Transform & Load loop shared by the import scripts
step_result.py  the typed result of each step, shown in the terminal and in the web app
"""
