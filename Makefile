.PHONY: dev verify test compile

dev:
	npm run dev

verify:
	npm run verify

test:
	python -m pytest

compile:
	python -m compileall backend
