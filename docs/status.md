# Status

## 0.1.0

Implemented: request parsing, Ollama transport, decision validation, bounded-root
file and directory creation, preview mode and replay records. The regression suite
uses an in-process HTTP server to exercise the transport without model weights.

Not yet verified: live model behavior and installation through Portage. Model
availability is not checked by CI. Replay records are protocol fixtures, not
recorded performance measurements.

Distribution work consists of an experimental overlay and source-build settings.
There is no bootable ISO, installer, kernel build, update channel or release key.
The amd64 badge describes the intended Gentoo baseline. The Python prototype is
not restricted to amd64.

CI checks userspace behavior on Linux and macOS. Badges shipped in this snapshot
are static metadata; they do not claim that a remote CI run has passed.
