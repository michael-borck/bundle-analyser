# bundle-analyser

Part of the **analyser family** — analyses collections of files in folders or zip archives.

Accepts a folder path or a zip file, walks all files, dispatches each to the appropriate
analyser family member (via `auto-analyser`), and returns per-file signals plus
structural signals about the collection as a whole.

## Status

Coming soon. Name reserved on PyPI.

## Analyser Family

| Tool | Input | Role |
|------|-------|------|
| `auto-analyser` | single file or zip | routes to the right specialist |
| `bundle-analyser` | folder or zip | walks a collection, calls auto-analyser per file |
| `git-analyser` | local git repo or remote URL | commit history + per-file signals |
| `code-analyser` | source file | Python, JS, TS, HTML, CSS, SQL signals |
| `document-analyser` | document file | PDF, DOCX, Markdown signals |

## Port

`8008` (reserved)
