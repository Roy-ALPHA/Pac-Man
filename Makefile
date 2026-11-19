config_file = config.json
.PHONY: build

install:
	@uv sync

run:
	@uv run pac_man.py $(config_file)

debug:
	@uv run python -m pdb pac_man.py $(config_file)

clean:
	@rm -rf __pycache__ .mypy_cache src/__pycache__ src/ui/__pycache__
	@rm -rf build dist

lint:
	@uv run flake8 .
	@uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

build:
	@uv run python -m PyInstaller PacMan.spec
