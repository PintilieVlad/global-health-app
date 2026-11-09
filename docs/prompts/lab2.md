# Prompts – Lab 2

This file lists, in order, every prompt I sent to an AI assistant for Lab 2. The assistant
was Claude in the Claude desktop app. It worked agentically:

- it read the lab handout and the reference repository linked in it;
- it wrote and tested the code in its own workspace, against a PostgreSQL database set up
  like mine after Lab 1;
- it copied the files into this project and wrote helper scripts, which are not committed,
  that I ran in Terminal on my Mac.

The first script upgraded the database, ran the notebook, which downloaded the data,
imported everything twice, and ran the checks. A second script rebuilt the commits (Prompt 3).
The assistant read the outputs and wrote the results. I did not write any Lab 2 code without
the assistant. During the work it also asked my permission to open the World Bank and WHO
websites in its browser, for the comparison in Task 2.4.

The repository has five Lab 2 commits:

1. "Lab 2: raw data extractors (WHO, World Bank, OWID)"
2. "Lab 2: raw-to-DB transform modules"
3. "Lab 2: observation cleaning module with IQR outlier flag"
4. "Lab 2: observation loader and per-source import scripts"
5. "Lab 2: exploration notebook, data quality checks and results"

## Prompt 1 – Lab 2 from the handout

- Tool and model: Claude (Anthropic), Claude desktop app, model `claude-opus-5-5`
- Date: 2026-11-04
- Prompt: `am primit continuarea cu lab 2` ("I received the continuation with lab 2"), with
  the handout attached (`Lab_2___CSP_in_Global_Health_Importing_cleaning_storing.pdf`)
- Result: the Lab 2 code, adapted to my topic (air pollution and respiratory disease):
  - extractors `etl/extract_who.py`, `etl/extract_worldbank.py`, `etl/extract_owid.py`,
    `etl/json_types.py` and `etl/raw_files.py` – commit 1;
  - transforms `etl/transform_*.py` – commit 2;
  - cleaning `etl/clean.py`, with the IQR flag of Task 2.2. It comes with the Alembic
    migrations (`alembic.ini`, `alembic/`: `0001` for the Lab 1 tables, `0002` for
    `is_outlier`), `app/models.py` (`Sex` and `ResidenceArea` enums, `is_outlier`),
    `app/create_tables.py`, `db/schema.sql` and `requirements.txt` – commit 3;
  - loader and imports `etl/load.py`, `etl/import_common.py`, `etl/import_worldbank.py`,
    `etl/import_who.py`, `etl/import_owid.py` and `app/database.py` (`get_engine`) – commit 4;
  - the notebook `notebooks/lab2_exploration.ipynb` (Task 2.1) and the queries
    `db/quality_checks.sql` – commit 5;
  - the first version of the new `README.md`.

  The assistant also wrote pytest tests and three helper scripts: one to download
  everything, one to run all imports and one to print the query results. Following
  Prompt 3, they are no longer in the repository.
- Your changes: none, the code is used as generated. I ran it on my computer: the tests
  passed, and the second import left the row counts unchanged. I kept these choices made by
  the assistant:
  - The `residence_area` column from Lab 1 stays in the natural key, so the duplicate check
    (query 2) also groups by it.
  - The WHO indicators stay in the import, although the WHO GHO API answered HTTP 503: the
    import skips them while the API is down.
  - The loop described in the handout as "shared by the three scripts" is written once, in
    `etl/import_common.py`.

## Prompt 2 – results after running the script

- Tool and model: Claude (Anthropic), Claude desktop app, model `claude-opus-5-5`
- Date: 2026-11-04
- Prompt: `gata` ("done"), sent after the helper script had finished in Terminal
- Result: `docs/lab2_results.md` (Tasks 2.2–2.4), the "Notes" cell of the executed notebook,
  the real import output in `README.md`, and this file – commit 5. The assistant
  independently recomputed the IQR counts from the raw files, and read the comparison
  values on the World Bank, Our World in Data and WHO websites.
- Your changes: none. The numbers in `docs/lab2_results.md` come from the output files of my
  run, which are not committed.

## Prompt 3 – fewer commits, only what each lab asks

- Tool and model: Claude (Anthropic), Claude desktop app, model `claude-opus-5-5`
- Date: 2026-11-04
- Prompt: `doamna profeesoara mi a zis ca in github ar trb mai putine commituri, ca am
  acoperit si laboraotarele viitoare` ("the professor told me there should be fewer commits
  on GitHub, as I had also covered the future labs"). The assistant then asked two questions
  and I chose these answers:
  - "Doar ce cere Lab 2, 5 commituri" ("only what Lab 2 asks, 5 commits");
  - "Da, curăță și Lab 1" ("yes, clean Lab 1 too").
- Result: the history was rebuilt and force-pushed.
  - **Lab 1 commit:** keeps only what Lab 1 asks. The web status page (`app/main.py`,
    `app/templates/*.html`), its test (`tests/test_api.py`) and the empty ETL modules were
    removed. Its README no longer describes them.
  - **Lab 2:** the eight earlier commits were regrouped into the five listed above, without
    the tests, the three helper scripts (`etl/download_all.py`, `etl/run_import.py`,
    `etl/check_quality.py`) and their mentions in the README and the results.
  - **What was removed is not lost.** It is kept on my Mac, outside the repository, for the
    later labs.
- Your changes: the two choices above, which I made after the professor's feedback.
