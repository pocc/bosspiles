#!/usr/bin/env bash
# Run the main script
.PHONY: run install kill test

install:
	@pip3 install -r requirements.txt
kill:
	@kill `cat pid` 2>/dev/null || true
run: kill
	@python3 -u bosspiles_discord.py >>errs 2>&1 & echo $$! > pid 
test:
	pytest tests.py
