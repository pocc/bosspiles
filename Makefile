#!/usr/bin/env bash
# Run the main script
.PHONY: run install kill test

install:
	@pip3 install -r requirements.txt
kill:
	@kill `cat pid` 2>/dev/null || true
run: kill
	@python3 -u bosspiles_discord.py 2>&1 & echo $$! > pid | tee -a errs 
test:
	pytest tests.py
