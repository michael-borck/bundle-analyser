# bundle-analyser

Part of the [analyser family](https://github.com/michael-borck/lens-analysers) — analyses collections of files in folders or zip archives.

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

## Local (CLI) routing

`bundle-analyser` dispatches every file through `auto-analyser`, whose built-in
defaults expect HTTP services on `localhost:800x`. For a fully local setup —
specialists installed in the same venv, invoked as CLIs — point `auto-analyser`
at them via `./auto-analyser.yaml` (beside where you run from) or
`~/.config/auto-analyser/config.yaml`:

```yaml
analysers:
  document-analyser: { type: cli, command: document-analyser }
  code-analyser: { type: cli, command: code-analyser }
  speech-analyser: { type: cli, command: speech-analyser }
  video-analyser: { type: cli, command: video-analyser }
  image-analyser: { type: cli, command: image-analyser }
  records-analyser: { type: cli, command: records-analyser }
  diagram-analyser: { type: cli, command: diagram-analyser }
```

Each listed member must expose the family contract: a `manifest` subcommand and
`<command> <file> --json` → JSON on stdout. Unlisted members keep the HTTP
defaults and error per-file when the service isn't running.
