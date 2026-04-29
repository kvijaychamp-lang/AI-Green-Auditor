# 📁 AI Green Auditor - Project Structure Guide

This document explains the recommended file structure for the AI Green Auditor project.

## 🗂️ Recommended Directory Structure

```
ai-green-auditor/
│
├── 📄 app.py                      # Main Streamlit application
├── 📄 requirements.txt            # Python dependencies
├── 📄 README.md                   # Project documentation
├── 📄 LICENSE                     # MIT License
├── 📄 .gitignore                  # Git ignore rules
├── 📄 STRUCTURE_GUIDE.md          # This file
│
├── 📁 assets/                     # Static assets (optional)
│   ├── 📁 images/
│   │   ├── logo.png
│   │   └── banner.png
│   └── 📁 screenshots/
│       ├── dashboard.png
│       ├── analytics.png
│       └── report.png
│
├── 📁 docs/                       # Additional documentation (optional)
│   ├── user_guide.md
│   ├── api_reference.md
│   └── contributing.md
│
├── 📁 tests/                      # Unit tests (optional)
│   ├── __init__.py
│   ├── test_calculations.py
│   └── test_validation.py
│
├── 📁 scripts/                    # Utility scripts (optional)
│   ├── run_app.bat               # Windows batch file
│   ├── run_app.sh                # Linux/Mac shell script
│   └── setup.py                  # Setup script
│
└── 📁 data/                       # Sample data (optional)
    ├── sample_reactions.csv
    └── test_cases.json
```

## 📝 File Descriptions

### Core Files (Required)

#### `app.py`
- **Location**: Root directory
- **Purpose**: Main Streamlit application file
- **Contains**: All application logic, UI components, calculations, and validations

#### `requirements.txt`
- **Location**: Root directory
- **Purpose**: Lists all Python dependencies
- **Usage**: `pip install -r requirements.txt`

#### `README.md`
- **Location**: Root directory
- **Purpose**: Project documentation and introduction
- **Audience**: GitHub visitors, contributors, users

#### `.gitignore`
- **Location**: Root directory
- **Purpose**: Specifies files/folders to exclude from Git
- **Includes**: `__pycache__/`, `.venv/`, `.env`, IDE folders

#### `LICENSE`
- **Location**: Root directory
- **Purpose**: MIT License for open-source distribution

### Optional Directories

#### `assets/`
Store static files like images, logos, and screenshots:
```
assets/
├── images/          # Logos, icons, banners
└── screenshots/     # Application screenshots for README
```

#### `docs/`
Additional documentation:
```
docs/
├── user_guide.md           # Detailed user instructions
├── api_reference.md        # Function documentation
├── contributing.md         # Contribution guidelines
└── changelog.md            # Version history
```

#### `tests/`
Unit tests for validation:
```
tests/
├── __init__.py
├── test_calculations.py    # Test calculation functions
├── test_validation.py      # Test validation logic
└── test_ui.py             # Test UI components
```

#### `scripts/`
Utility scripts for easy execution:
```
scripts/
├── run_app.bat            # Windows: Double-click to run
├── run_app.sh             # Linux/Mac: ./run_app.sh
└── install_deps.bat       # Windows: Install dependencies
```

#### `data/`
Sample data and test cases:
```
data/
├── sample_reactions.csv   # Example reaction data
├── test_cases.json        # Validation test cases
└── solvents_db.json       # Solvent toxicity database
```

## 🚀 Quick Setup Instructions

### For Windows Users

1. **Create a batch file** (`run_app.bat`) in the `scripts/` folder:
```batch
@echo off
echo Starting AI Green Auditor...
cd ..
streamlit run app.py
pause
```

2. **Double-click** `run_app.bat` to launch the application

### For Linux/Mac Users

1. **Create a shell script** (`run_app.sh`) in the `scripts/` folder:
```bash
#!/bin/bash
echo "Starting AI Green Auditor..."
cd "$(dirname "$0")/.."
streamlit run app.py
```

2. **Make it executable**:
```bash
chmod +x scripts/run_app.sh
```

3. **Run the script**:
```bash
./scripts/run_app.sh
```

## 📦 Deployment Structure

### For GitHub Repository
```
ai-green-auditor/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── assets/
    └── screenshots/
```

### For Production Deployment (e.g., Streamlit Cloud)
```
ai-green-auditor/
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml        # Streamlit configuration
└── README.md
```

## 🔧 Configuration Files

### `.streamlit/config.toml` (Optional)
Create this for custom Streamlit settings:
```toml
[theme]
primaryColor = "#00e5ff"
backgroundColor = "#0a1628"
secondaryBackgroundColor = "#1a2a6c"
textColor = "#e0e0e0"
font = "sans serif"

[server]
headless = true
port = 8501
```

## 📊 Best Practices

### ✅ Do's
- Keep `app.py` in the root directory
- Use `requirements.txt` for all dependencies
- Add comprehensive `.gitignore` rules
- Include screenshots in `assets/screenshots/`
- Document all major functions
- Use semantic versioning (v1.0.0)

### ❌ Don'ts
- Don't commit `.env` files with secrets
- Don't include large binary files
- Don't commit `__pycache__/` folders
- Don't hardcode file paths
- Don't commit generated PDFs
- Don't include IDE-specific files

## 🔄 Version Control Workflow

1. **Initialize Git**:
```bash
git init
git add .
git commit -m "Initial commit: AI Green Auditor v1.0.0"
```

2. **Create GitHub Repository**:
```bash
git remote add origin https://github.com/yourusername/ai-green-auditor.git
git branch -M main
git push -u origin main
```

3. **Update and Push Changes**:
```bash
git add .
git commit -m "Add feature: Toxicity assessment"
git push origin main
```

## 📱 Minimal Structure (For Quick Start)

If you want to keep it simple:
```
ai-green-auditor/
├── app.py              # Main application
├── requirements.txt    # Dependencies
├── README.md          # Documentation
└── .gitignore         # Git rules
```

This is sufficient for a functional GitHub repository!

## 🎯 Summary

- **Root files**: `app.py`, `requirements.txt`, `README.md`, `.gitignore`, `LICENSE`
- **Optional folders**: `assets/`, `docs/`, `tests/`, `scripts/`, `data/`
- **Batch files**: Place in `scripts/` folder, not root
- **Screenshots**: Place in `assets/screenshots/` for README
- **Keep it clean**: Use `.gitignore` to exclude temporary files

---

**Happy Coding! 🚀**
