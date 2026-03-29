# Build system for the project

PYTHON = python3
BUILD_DIR = build

.PHONY: all clean

all: build/output.txt

build/output.txt: build/lint_report.txt build/config.json build/templates.txt
	$(PYTHON) src/build_report.py $@

build/templates.txt: build/config.json
	$(PYTHON) src/compile_templates.py build/config.json $@

build/lint_report.txt:
	$(PYTHON) src/lint.py $@

build/config.json:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) src/gen_config.py $(BUILD_DIR)/config.json

clean:
	rm -rf $(BUILD_DIR)
