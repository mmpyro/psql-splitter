.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make run   - Run the SQL splitter on the example file"
	@echo "  make test  - Run unit tests"
	@echo "  make clean - Remove generated SQL chunks"

.PHONY: clean
clean:
	@echo "Cleaning up..."
	@rm -f [0-9]*.sql

.PHONY: run
run: clean
	@echo "Running SQL splitter..."
	time uv run psql-splitter -f test_dump.sql -n 3

.PHONY: test
test:
	@echo "Running unit tests..."
	uv run pytest src/tests -v
