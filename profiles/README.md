# Build configuration

`make.conf.example` is a fragment for an existing Gentoo installation. It is not
a selectable Portage profile. Merge individual settings with `/etc/portage/make.conf`;
do not replace the host configuration wholesale.

The baseline is amd64, glibc and OpenRC. Package builds use local sources. The
inference service is outside Portage's build environment. Its model weights are
distributed separately and are not compiled by this tree.

No kernel configuration, stage3 manifest or image builder is provided yet.
