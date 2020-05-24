#!/usr/bin/env bash
# Run the main script
.PHONY: run clean

clean:
	@printf "" > errs
run: clean
	@python3 -u client.py 2>&1 | tee errs &