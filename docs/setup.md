# Setup

## Userspace tools

Run from the checkout with Python 3.11 or later. To stage an installation for
inspection:

```sh
make install DESTDIR="$PWD/var/stage" PREFIX=/usr
./var/stage/usr/bin/ambimk --help
```

For a user installation, use `make install PREFIX="$HOME/.local"` and add
`$HOME/.local/bin` to PATH. The command is installed as `ambimk`.

For live requests, provision an Ollama-supported GPU with at least 2 GiB of
available VRAM, install Ollama separately, start its local service and pull
`smollm2:135m`. The 2 GiB figure is the AmbiguOS hardware baseline, allowing room
for weights, context and runtime overhead; it is not a measured model minimum.
The prototype does not enforce GPU placement. Confirm GPU use with `ollama ps`
while a live request is running. The prototype does not download weights or start services.
`etc/ambiguos.env` supplies example environment settings. It is not loaded
automatically. Both variables can also be set directly in the shell; CLI options
take precedence. There is no background daemon in this tree.

## Gentoo overlay

The overlay contains a live ebuild with no stable keywords. It is a packaging
scaffold and has not been validated by a Portage build. Once this repository has
a remote, set `AMBIGUOS_GIT_URI` in Portage's environment to that URL and register
the local `overlay/` directory in repos.conf. The overlay requires the Gentoo
master repository. Accept the live package explicitly before attempting an emerge.

Do not point git-r3 at `overlay/`: it needs the full source repository. The ebuild
fetches the branch's current head; it does not provide reproducible releases.
The inference service and model are provisioned separately.
