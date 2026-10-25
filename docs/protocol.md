# Decision protocol, version 1

Requests contain `version`, `path`, `kind` and `context`. Decisions contain exactly
`version`, `action`, `path` and `reason`. Unknown fields are rejected.

```json
{"version": 1, "action": "directory", "path": "notes", "reason": "A collection is indicated."}
```

`version` must be the integer 1. `action` is `file`, `directory` or `defer`.
`path` is a relative POSIX path, up to 4096 characters. Empty components, dot
components, control characters and backslashes are rejected. `reason` is a
nonempty string of at most 1024 characters. The entire response is limited to
65536 bytes. Markdown fences are not part of the protocol.

The Ollama adapter uses `POST /api/generate`, `stream: false` and `format: json`.
The JSON string in the response's `response` field is validated as a decision.
There is a 120-second timeout by default; use `--timeout` to change it.

The CLI prints one JSON result on stdout. Errors go to stderr. Exit codes are 0
for an accepted operation or preview, 1 for an error and 3 for a deferred decision.
A preview validates the destination without writing to it. It still invokes the
model unless `--replay` is selected.
