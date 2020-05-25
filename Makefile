#!/usr/bin/env bash
# Run the main script
.PHONY: run install clean test

clean:
	@printf "" > errs
install:
	@pip3 install -r requirements.txt
run: clean
	@python3 -u client.py 2>&1 | tee errs &
test:
	pytest tests.py