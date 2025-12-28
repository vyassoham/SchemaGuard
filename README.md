# UniSchema

<div align="center">

# 🔍 UniSchema

**Universal Data Validation & Quality Analysis Engine**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

*A production-ready Python library for validating structured data from multiple file formats using a unified schema definition.*

[Features](#features) •
[Installation](#installation) •
[Quick Start](#quick-start) •
[Documentation](#documentation) •
[Examples](#examples)

</div>

---

## 📋 Overview

**UniSchema** is a universal data validation engine that enables you to validate structured data coming from **multiple file types** using a **single schema definition**. Whether your data is in CSV, Excel, JSON, or PDF format, UniSchema provides consistent validation, quality analysis, and comprehensive reporting.

### The Problem

Data comes in many formats. Teams often struggle with:

- Different validation logic for each file type
- Inconsistent error reporting across formats
- Lack of visibility into data quality issues
- Time-consuming manual data inspection

### The Solution

UniSchema solves these problems by:

- ✅ **Unified Validation**: One Pydantic schema validates all formats
- ✅ **Comprehensive Analysis**: Automatic data quality metrics
- ✅ **Visual Reports**: Publication-ready charts and graphs
- ✅ **Easy Integration**: Both CLI and Python API available

---

## ✨ Features

### 🔄 Multi-Format Support

| Format | Extension | Features |
|--------|-----------|----------|
| CSV | `.csv`, `.tsv` | Auto-delimiter detection, encoding options |
| Excel | `.xlsx`, `.xls` | Multi-sheet support, sheet selection |
| JSON | `.json`, `.jsonl` | Nested structure flattening, JSONL support |
| PDF | `.pdf` | Table extraction from structured PDFs |

### 📊 Data Quality Analysis

- **Missing Value Analysis**: Per-column null counts and percentages
- **Duplicate Detection**: Identify and count duplicate rows
- **Statistical Metrics**: Mean, median, std, quartiles for numeric columns
- **Completeness Scoring**: Overall data quality percentage

### 📈 Visualization Suite

All visualizations are generated using **matplotlib only** (no seaborn):

- **Error Bar Charts**: Validation errors per column
- **Pie Charts**: Valid vs. invalid row distribution
- **Missing Value Heatmaps**: Visual representation of null patterns
- **Distribution Histograms**: Numeric column distributions
- **Correlation Matrices**: Relationship between numeric columns
- **Box Plots**: Outlier detection visualization

### 🛡️ Schema Validation

Built on **Pydantic v2** for robust validation:

- Type checking
- Range constraints
- Required/optional fields
- Email validation
- Custom validators
- Detailed error messages

---

## 🚀 Installation

### Using pip

```bash
pip install -r requirements.txt
```

### From Source

```bash
git clone https://github.com/yourusername/unischema.git
cd unischema
pip install -r requirements.txt
```

### PDF Support (Optional)

For PDF table extraction, you also need Java installed:

```bash
# Windows (using chocolatey)
choco install openjdk

# macOS
brew install openjdk

# Ubuntu/Debian
sudo apt install default-jdk
```

---

## 📖 Quick Start

### Command Line Interface

```bash
# Validate a CSV file
python -m unischema.cli check --file data/users.csv --schema user

# Validate and generate reports
python -m unischema.cli check --file data/users.csv --schema user --output ./outputs

# Get file information
python -m unischema.cli info --file data/users.csv

# List available schemas
python -m unischema.cli schemas
```

### Python API

```python
from unischema.main import validate_file

# Simple validation
result = validate_file(
    file_path="data/users.csv",
    schema_name="user",
    output_dir="outputs/",
    print_summary=True
)

print(f"Valid rows: {result['valid_count']}")
print(f"Invalid rows: {result['invalid_count']}")
print(f"Success rate: {result['success_rate']:.1f}%")
```

### Programmatic Usage

```python
from unischema.loaders import LoaderFactory
from unischema.validator import UniversalValidator
from unischema.schema import UserSchema

# Load data from any supported format
df = LoaderFactory.load("data/users.csv")

# Validate with schema
validator = UniversalValidator(UserSchema)
result = validator.validate(df)

# Access results
clean_data = result.valid_df
invalid_data = result.invalid_df
errors = result.errors

# Print error details
for error in errors[:5]:
    print(f"Row {error.row_index}, {error.column}: {error.message}")
```

---

## 🏗️ Architecture

```
unischema/
│
├── loaders/                 # Data Loading Layer
│   ├── base_loader.py       # Abstract base class
│   ├── csv_loader.py        # CSV/TSV loading
│   ├── excel_loader.py      # Excel with multi-sheet
│   ├── json_loader.py       # JSON with flattening
│   ├── pdf_loader.py        # PDF table extraction
│   └── loader_factory.py    # Automatic loader selection
│
├── schema/                  # Schema Definitions
│   └── user_schema.py       # Pydantic models
│
├── validator/               # Validation Engine
│   └── validator.py         # Core validation logic
│
├── analysis/                # Quality Analysis
│   ├── metrics.py           # Data quality metrics
│   └── summary.py           # Report generation
│
├── visualize/               # Visualization
│   ├── error_plots.py       # Error visualizations
│   ├── missing_plots.py     # Missing data plots
│   ├── distribution_plots.py # Distribution charts
│   └── report_generator.py  # Orchestrates all plots
│
├── outputs/                 # Generated Outputs
│   ├── plots/               # PNG visualizations
│   └── reports/             # JSON/CSV reports
│
├── cli.py                   # Command-line interface
├── main.py                  # Main entry point
├── requirements.txt         # Dependencies
└── README.md                # Documentation
```

### Design Principles

1. **Separation of Concerns**: Loading, validation, and visualization are independent
2. **Format Agnostic**: All data converts to pandas DataFrame for unified processing
3. **Schema-Driven**: Pydantic defines the single source of truth
4. **Extensible**: Easy to add new loaders or schemas

---

## 📋 Schema Examples

### User Schema

```python
from pydantic import BaseModel, Field

class UserSchema(BaseModel):
    id: int = Field(..., gt=0, description="Unique user ID")
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., description="Valid email address")
    age: int | None = Field(None, ge=0, le=120)
    phone: str | None = Field(None, min_length=10, max_length=15)
    is_active: bool = Field(default=True)
```

### Employee Schema

```python
class EmployeeSchema(BaseModel):
    employee_id: int = Field(..., gt=0)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: str
    department: str = Field(..., min_length=2)
    salary: float = Field(..., gt=0)
    hire_date: date
    is_full_time: bool = Field(default=True)
```

### Custom Schema

```python
from unischema.main import register_schema

class ProductSchema(BaseModel):
    sku: str = Field(..., pattern=r"^[A-Z]{3}-\d{4}$")
    name: str = Field(..., min_length=3)
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)

register_schema("product", ProductSchema)
```

---

## 📊 Output Examples

### Terminal Output

```
============================================================
  VALIDATION SUMMARY REPORT
============================================================

  📄 Schema: UserSchema
  📁 Source: data/users.csv
  🕐 Generated: 2024-01-15 14:30:22

------------------------------------------------------------
  VALIDATION RESULTS
------------------------------------------------------------

  Total Rows:     1,000
  ✅ Valid Rows:   847 (84.7%)
  ❌ Invalid Rows: 153 (15.3%)

------------------------------------------------------------
  ERRORS BY COLUMN
------------------------------------------------------------

  email                   78 ██████████████████████████████
  age                     45 ███████████████
  phone                   30 ██████████

------------------------------------------------------------
  DATA QUALITY METRICS
------------------------------------------------------------

  Completeness Score: 94.2%
  Duplicate Rows:     12 (1.2%)

============================================================
```

### Generated Files

```
outputs/
├── plots/
│   ├── errors_by_column.png      # Bar chart of errors
│   ├── valid_invalid_pie.png     # Pie chart
│   ├── error_types.png           # Error type breakdown
│   ├── missing_heatmap.png       # Missing value heatmap
│   ├── missing_bar.png           # Missing value bar chart
│   ├── numeric_distributions.png # Histograms
│   ├── boxplot.png               # Box plots
│   └── correlation_matrix.png    # Correlation heatmap
│
└── reports/
    ├── validation_report_*.json  # Full JSON report
    ├── valid_data_*.csv          # Clean data
    └── invalid_data_*.csv        # Rows with errors
```

---

## ⚠️ Limitations

### PDF Handling

PDF table extraction has inherent limitations:

- **Structured Tables Only**: Works best with clearly defined table borders
- **Java Required**: tabula-py requires Java to be installed
- **No OCR**: Cannot extract from scanned/image-based PDFs
- **Complex Layouts**: May struggle with merged cells or nested tables
- **Accuracy**: Results depend on PDF structure quality

**Recommendations for PDFs:**
1. Use text-based PDFs when possible
2. Verify extracted data manually on first use
3. Consider converting to CSV/Excel for critical data
4. Use `lattice=True` option for tables with visible borders

### General Limitations

- Large files (>1M rows) may require chunked processing
- Nested JSON is flattened to tabular format
- Binary columns are not validated

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/yourusername/unischema.git
cd unischema
pip install -r requirements.txt
pip install pytest pytest-cov black isort mypy
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with these excellent libraries:

- [pandas](https://pandas.pydata.org/) - Data manipulation
- [numpy](https://numpy.org/) - Numerical computing
- [pydantic](https://pydantic.dev/) - Data validation
- [matplotlib](https://matplotlib.org/) - Visualization
- [tabula-py](https://github.com/chezou/tabula-py) - PDF extraction

---

<div align="center">

**Made with ❤️ for data quality**

[⬆ Back to Top](#unischema)

</div>
