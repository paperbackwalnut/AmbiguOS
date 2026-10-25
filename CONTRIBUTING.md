# Contributing

Keep changes small enough to review without reproducing a full system build.
Run `make check`. A change to the decision schema requires a protocol version
change and an updated replay record.

For inference reports, include the model tag, request, returned JSON and whether
the operation was applied. A difference between requested and inferred kind is
not sufficient on its own; explain which context was interpreted incorrectly.
Do not submit credentials, personal paths or private request context.

Use a subject such as `intent: reject empty path components`. Avoid unrelated
formatting changes. Packaging changes should include the Portage version and
build log. Do not mark an architecture stable without a native build.
