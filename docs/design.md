# Design notes

## Scope

Portage owns dependency resolution and compilation. The intent layer owns the
interpretation of creation requests. Keeping these separate allows source builds
to remain deterministic while filesystem semantics can be revised independently.

The current implementation has one entry point, `ambimk`. It does not intercept
system calls, alter libc or wrap `mkdir`, `touch`, `mknod` or `mkfs`. Device nodes
and filesystems are outside protocol version 1.

## Decision path

1. Parse the caller's request and reject invalid request paths.
2. Send the request to the configured inference service, or load a replay record.
3. Validate the decision's fields and relative path.
4. Check the destination and create the selected object.

The response may change both kind and name. The caller's declared kind is
advisory. There is no lexical fallback when inference fails. Malformed responses
fail the request; they are not repaired by another model.

`defer` is terminal for the invocation. Repeating the command starts a new
interpretation. Retries are the caller's responsibility.

## Execution limits

Files are empty and created exclusively. Directories are created without replacing
existing paths. Missing parents are created after validation. A failed operation
may leave parent directories behind. Permissions follow the process umask.

Symlink checks prevent ordinary redirection outside the root, including symlinks
in the root's own path. These checks are not atomic with creation. A private root
with no concurrent writers is required; the executor is not a hostile-user sandbox.
Hard links already present at the destination are rejected as existing paths.

No request is sent until the caller invokes the tool. Only the supplied path,
kind and context are sent; directory contents and environment variables are not.
The API origin is restricted to loopback HTTP, proxies are disabled and redirects
are refused. A local service may have its own downstream network behavior.
