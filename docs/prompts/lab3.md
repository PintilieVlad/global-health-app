# Prompts – Lab 3

This file lists, in order, every prompt I sent to an AI assistant for Lab 3. The assistant
was Claude in the Claude desktop app, and it worked agentically:

- It read the lab handout and the reference repository linked in it.
- It wrote the code in its own workspace and tested it there, on a copy of my raw data
  files.
- It prepared the commits and a helper script, which is not committed. I ran the script in
  the VS Code terminal on my Mac.
- It opened the running application in its browser to take the screenshots.

I did not write any Lab 3 code without the assistant.

The Lab 3 commits are:

1. "Lab 3: import scripts return results through import_all()"
2. "Lab 3: domain types and observation repository"
3. "Lab 3: observation and ETL services"
4. "Lab 3: controllers, templates and dependency wiring"
5. "Lab 3: tests for the repository, service and controller layers"
6. "Lab 3: sex filter through all layers"
7. "Lab 3: results, prompts and README"

## Prompt 1 – Lab 3 from the handout

- Tool and model: Claude (Anthropic), Claude desktop app, model `claude-opus-5-5`
- Date: 2026-11-13
- Prompt: `labul 3` ("lab 3"), with the handout attached
  (`Lab_3___CSP_in_Global_Health_Server_side_rendering_and_layers.pdf`)
- Result: the code of commits 1–6, adapted to my project. The adaptations were my
  indicators, the residence-area column, the outlier count in the import results, and
  `etl/import_runner.py` in place of my Lab 2 `etl/import_common.py`.
  - **Commit 1.** `etl/step_result.py`, `etl/import_runner.py`, and `import_all()` in the
    three import scripts. The notebook `notebooks/lab2_exploration.ipynb` was updated to
    the renamed fields; its outputs are the ones from the Lab 2 run.
  - **Commit 2.** `app/domain.py` and `app/repositories/observation_repository.py`.
    `app/models.py` now reads `sex` and `residence_area` back as enum members.
  - **Commit 3.** `app/services/observation_service.py` and
    `app/services/etl_service.py`.
  - **Commit 4.** The controllers, the three templates, `app/dependencies.py` and
    `app/main.py`. `app/database.py` was changed to build the engine and the sessions
    lazily, and `alembic/env.py` and `app/create_tables.py` were adapted to it.
  - **Commit 5.** `pytest.ini`, `tests/conftest.py` (temporary schema, seed data), one test
    file per layer, `tests/test_architecture.py` (Task 3.4), and `httpx2` in
    `requirements.txt`.
  - **Commit 6.** Task 3.3: the sex filter in the domain, repository, service, controller
    and view, with its tests.

  I ran the helper script on my Mac. It added these commits under my name, ran the tests
  (64 passed) and the Task 3.4 demonstration, and started the application.
- Your changes: none, the code is used as generated.

## Prompt 2 – the application running

- Tool and model: Claude (Anthropic), Claude desktop app, model `claude-opus-5-5`
- Date: 2026-11-17
- Prompt: `i imi apare asra si nmc altceva` ("and this shows up and nothing else"), with a
  screenshot of the VS Code terminal. The screenshot showed uvicorn's
  `Application startup complete`. The assistant then asked whether it could click
  *Transform & load* in the running application, and I answered
  "Da, apasă tu" ("yes, you click it").
- Result: the four screenshots in `docs/img/`, taken in the assistant's browser on my Mac.
  They are the two filter combinations, page 2 of the region filter, and the
  *Transform & load* result. The assistant also wrote `docs/lab3_results.md` from the
  outputs of my run (tests, Task 3.4 demonstration, versions) and updated `README.md` and
  this file – commit 7.
- Your changes: none.
