# Clinic Visit Sorter

Educational, non-diagnostic prototype. It does not diagnose, provide medical advice, or remove students from the queue. A nurse must review every student and make all medical decisions.

## Files
- `specification.pdf` — your supplied project specification.
- `system_prompt.txt` — your supplied system prompt.
- `clinic_sorter.py` — your supplied main Python program.
- `eval_harness.py` — your supplied evaluation tests.
- `red_team_tests.py` — your supplied red-team tests.
- `visits.csv` — sample input data created for this project.

## Run in VS Code (Windows PowerShell)
Open this folder in VS Code, then choose Terminal > New Terminal.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
python -m unittest eval_harness -v
python -m unittest red_team_tests -v
python clinic_sorter.py
```

The program can use its offline fallback without an API key. To enable its optional OpenAI mode, set `OPENAI_API_KEY` in the terminal session. Never put your API key in this folder or commit it to GitHub.

## Important review note
The supplied `clinic_sorter.py` has been kept unchanged. Its current summary report counts priorities and categories but does not yet include hourly counts, although the project specification asks for them. Review this requirement before final submission. The tests are software checks only; they do not establish clinical accuracy or safety.
