# bundle-analyser — basic usage

bundle-analyser walks a folder or zip archive, runs `auto-analyser` on each file, and aggregates the results into a single bundle report.

## Prerequisite

bundle-analyser shells out to `auto-analyser` per file, so `auto-analyser` must be installed and on your `PATH`:

```bash
pip install auto-analyser
```

## Install

```bash
pip install bundle-analyser
```

## CLI

```bash
# Analyse every file in a folder
bundle-analyser path/to/folder --json

# Analyse the contents of a zip archive
bundle-analyser submission.zip --json
```

Without `--json` you get a Rich summary (file counts and an extension distribution table).

## Python

```python
from bundle_analyser.core import analyse_bundle

result = analyse_bundle("path/to/folder")  # or "submission.zip"
print(result.total_files, result.analysed_files)
print(result.file_type_distribution)
```

## HTTP

```bash
bundle-analyser serve   # http://127.0.0.1:8008
```

```bash
# Analyse a local path
curl -X POST http://127.0.0.1:8008/analyse \
  -H "Content-Type: application/json" \
  -d '{"path": "path/to/folder"}'

# Or upload a zip archive
curl -F "file=@submission.zip" http://127.0.0.1:8008/analyse/upload
```
