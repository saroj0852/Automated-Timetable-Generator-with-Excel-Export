# Time Management Software

This project generates university timetables using Python and Node.js, and outputs both JSON and PDF files.

## Folder Structure

- `src/python/` — Python scripts (main: `table.py`)
- `src/js/` — JavaScript scripts (`labassign.js`, `timetable_resolve.js`, `json2pdf.js`)
- `src/output/` — All generated JSON files
- `src/` — Generated PDF timetable

## Prerequisites

- **Python 3.8+** ([Download & Install](https://www.python.org/downloads/))
- **Node.js 16+** ([Download & Install](https://nodejs.org/en/download/))

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd Time-Management-Software
   ```

2. **Install Python packages**
   ```bash
   pip install -r constraints.txt
   # or
   pip install ortools pandas
   ```

3. **Install Node.js packages**
   ```bash
   npm install
   # If you see missing package errors, install them manually:
   npm install pdfmake
   ```

## Usage

You can run the full pipeline using either the batch or shell script:

### On Linux/macOS
```bash
chmod +x generate.sh
bash generate.sh
```

### On Windows
```cmd
generate.bat
```

This will:
1. Generate the master timetable (Python)
2. Assign labs (Node.js)
3. Resolve timetable conflicts (Node.js)
4. Generate a PDF (Node.js)

## Output
- All JSON files are saved in `src/output/`
- The final PDF (`Timetable.pdf`) is saved in `src/`

## Viewing the PDF
Open `src/output/Timetable.pdf` with any PDF viewer.

## Troubleshooting
- Ensure Python and Node.js are installed and available in your PATH.
- If you encounter missing package errors, install them as shown above.

## License
MIT
