PYTHON ?= python3
PREFIX ?= /usr/local

.PHONY: check install
check:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

install:
	install -d "$(DESTDIR)$(PREFIX)/lib/ambiguos/ambiguos" "$(DESTDIR)$(PREFIX)/bin"
	install -m 644 src/ambiguos/*.py "$(DESTDIR)$(PREFIX)/lib/ambiguos/ambiguos/"
	install -m 755 scripts/ambimk-installed "$(DESTDIR)$(PREFIX)/bin/ambimk"
