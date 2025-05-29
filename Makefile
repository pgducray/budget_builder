# Python configuration
PYTHON := PYTHONPATH=. python3
VENV := .venv

# Paths
SCRIPT_PATH := src/data_processing/process_all_statements.py
CATEGORIZE_SCRIPT := src/categorize_transactions.py
RAW_DIR := data/raw
PROCESSED_DIR := data/processed
OUTPUT_FILE := data/transactions.csv
CATEGORIZED_FILE := data/categorized_transactions.csv

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make process    - Process all statements in data/raw"
	@echo "  make categorize - Process statements and categorize transactions"
	@echo "  make setup     - Create required directories"
	@echo "  make clean     - Remove processed files"
	@echo "  make validate  - Check if required directories exist"
	@echo "  make help      - Show this help message"

# Main targets
.PHONY: process categorize setup validate clean

process: validate
	$(PYTHON) $(SCRIPT_PATH)

categorize: process
	$(PYTHON) $(CATEGORIZE_SCRIPT)

setup:
	mkdir -p $(RAW_DIR) $(PROCESSED_DIR)

validate:
	@test -d $(RAW_DIR) || (echo "Error: $(RAW_DIR) directory not found" && exit 1)
	@test -d $(PROCESSED_DIR) || (echo "Error: $(PROCESSED_DIR) directory not found" && exit 1)

clean:
	rm -f $(OUTPUT_FILE) $(CATEGORIZED_FILE)
	rm -rf $(PROCESSED_DIR)/*
