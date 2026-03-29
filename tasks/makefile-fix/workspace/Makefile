# Build system for the project
# BUG 1: No .PHONY declarations - 'build' target conflicts with 'build/' directory
# BUG 2: output.txt depends on templates.txt, but templates depends on config,
#         and the dependency chain is wrong
# BUG 3: $(SOURCES) variable is never defined, so lint gets empty file list
# BUG 4: clean doesn't remove templates.txt
# BUG 5: config target writes to wrong path (build/conf.json instead of build/config.json)

PYTHON = python3
BUILD_DIR = build

all: build/output.txt

build/output.txt: build/lint_report.txt build/templates.txt
	$(PYTHON) src/build_report.py $@

build/templates.txt: build/config.json
	$(PYTHON) src/compile_templates.py build/conf.json $@

build/lint_report.txt:
	$(PYTHON) src/lint.py $@

config:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) src/gen_config.py $(BUILD_DIR)/conf.json

build/config.json: config

clean:
	rm -rf $(BUILD_DIR)/output.txt $(BUILD_DIR)/lint_report.txt $(BUILD_DIR)/config.json
