EAPI=8

PYTHON_COMPAT=( python3_{11..13} )
inherit python-single-r1 git-r3

DESCRIPTION="Intent-mediated filesystem creation tools"
EGIT_REPO_URI="${AMBIGUOS_GIT_URI}"
LICENSE="MIT"
SLOT="0"
REQUIRED_USE="${PYTHON_REQUIRED_USE}"
RDEPEND="${PYTHON_DEPS}"
DEPEND="${PYTHON_DEPS}"

pkg_setup() {
    [[ -n ${AMBIGUOS_GIT_URI} ]] || die "Set AMBIGUOS_GIT_URI to the published repository URL"
    python-single-r1_pkg_setup
}

src_test() {
    PYTHONPATH=src "${PYTHON}" -m unittest discover -s tests -v || die
}

src_install() {
    emake DESTDIR="${D}" PREFIX=/usr install
    python_fix_shebang "${ED}/usr/bin/ambimk"
    dodoc README.md CHANGELOG.md
}
