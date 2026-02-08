# SQL Splitter 🚀

A high-performance command-line tool designed to split massive SQL dump files into smaller, manageable chunks. Unlike simple line-based splitters, **SQL Splitter** respects SQL statement boundaries (using separators like `;`) to ensure each chunk remains a valid SQL script.

---

## ✨ Features

- **Smart Splitting**: Splits files based on size while respecting SQL statement integrity.
- **Compression**: Optionally remove comments and empty lines to reduce chunk size.
- **Configurable**: Define custom separators, single-line comment markers, and multi-line comment markers.
- **Fast & Efficient**: Processes files line-by-line using streaming I/O, minimizing memory usage for multi-gigabyte files.

---

## 🛠 Prerequisites

- **Python**: 3.13 or higher.
- **uv**: Recommended for dependency management (fast, reliable).

---

## 🚀 Installation & Setup

We use `uv` for easy environment management.

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd sql_splitter
    ```

2.  **Sync dependencies**:
    ```bash
    uv sync
    ```

---

## 📖 Usage Guide

### Command Line Arguments

Run the tool using `uv run psql-splitter`.

| Argument | Long Flag | Required | Default | Description |
| :------- | :-------- | :------- | :------ | :---------- |
| `-f`     | N/A       | Yes      | -       | Path to the source SQL file. |
| `-n`     | N/A       | Yes      | -       | Number of chunks to split the file into. |
| `-s`     | N/A       | No       | `;`     | SQL statement separator. |
| `-c`     | N/A       | No       | `--`    | Single-line comment character. |
| `-m`     | N/A       | No       | `/*`    | Multi-line comment character start. |
| `-z`     | N/A       | No       | False   | Flag to compress output (removes empty lines/comments). |

### Examples

**Basic split into 5 chunks:**
```bash
uv run psql-splitter -f big_dump.sql -n 5
```

**Split with compression and custom separator:**
```bash
uv run psql-splitter -f my_data.sql -n 3 -s "$$" -z
```

---

## 🧑‍💻 Developer Guide

If you are a developer joining the project, here is how you can work with the codebase.

### Project Structure

```text
.
├── main.py              # CLI Entry point
├── Makefile             # Automated task runner
├── pyproject.toml       # Project metadata and dependencies
├── src/
│   ├── splitter.py      # Core splitting logic
│   └── tests/           # Unit tests
└── README.md            # This file
```

### Automation with Makefile

The project includes a `Makefile` for common tasks:

- **Run Example**:
  ```bash
  make run
  ```
  Runs the splitter on a `test_dump.sql` file (cleans previous chunks first).

- **Run Tests**:
  ```bash
  make test
  ```
  Executes the test suite using `pytest`.

- **Cleanup**:
  ```bash
  make clean
  ```
  Removes all generated `.sql` chunks (files matching `[0-9]*.sql`).

- **Help**:
  ```bash
  make help
  ```
  Lists available commands.

### Running Tests Manually

You can also run tests directly via `uv`:
```bash
uv run pytest src/tests -v
```

---

## 📝 How it works

1.  **Size Calculation**: The tool calculates the total file size and determines a target chunk size by dividing it by `-n`.
2.  **Streaming Read**: It reads the input file line-by-line to handle extremely large files without filling up RAM.
3.  **Statement Boundary**: It only closes a chunk if it has exceeded the target size **and** the current line ends with the specified separator (`-s`).
4.  **Compression Mode**: When `-z` is enabled, the tool skips lines that are empty or start with the specified comment characters (`-c` or `-m`).

---

## 📄 License

[MIT License](LICENSE)
