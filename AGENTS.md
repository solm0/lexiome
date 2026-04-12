## Run
source venv/bin/activate
uvicorn main:app --reload --port 8000

## Architecture
- FastAPI, SQLite
- json data: preprocessed corpus (NOT to be accessed directly)
- backend exposes API for all data access

## API rules
- Keep endpoints simple
- Do not change existing response formats unless necessary

## Editing rules
- Modify only relevant files
- Do not refactor unrelated code
- Do not scan the entire project