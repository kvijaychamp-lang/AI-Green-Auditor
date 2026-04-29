# 🌿 AI Green Auditor

A comprehensive web-based tool for evaluating chemical reaction sustainability using Green Chemistry principles and AI-powered analytics.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)

## 📋 Overview

The **AI Green Auditor** is a professional-grade application designed for chemists, researchers, and students to assess the environmental impact and sustainability of chemical reactions. Built with a modern dark blue aesthetic and scientific rigor, it provides real-time analytics, validation checks, and comprehensive reporting capabilities.

## ✨ Core Features

### 🤖 AI-Powered Analytics
- **E-Factor Gauge**: Real-time environmental factor calculation with visual indicators
- **Atom Economy Analysis**: Pie chart visualization showing material utilization vs waste
- **Efficiency Radar Chart**: Multi-dimensional sustainability metrics display
- **Dynamic Grade Badge**: A/B/C grading system with glowing visual feedback

### 🌱 12 Green Chemistry Principles
Interactive checklist covering all 12 principles:
- Prevention, Atom Economy, Less Hazardous Synthesis
- Designing Safer Chemicals, Safer Solvents, Energy Efficiency
- Renewable Feedstocks, Reduce Derivatives, Catalysis
- Design for Degradation, Real-time Pollution Prevention
- Safer Chemistry for Accident Prevention

### 📊 Sustainability Impact Dashboard
Four-column metric display:
- **Waste Prevented**: Comparison vs traditional methods
- **CO₂ Reduced**: Carbon footprint impact
- **Ecological Impact**: Trees equivalent calculation
- **Toxicity Level**: Color-coded hazard assessment (Low/Moderate/High)

### 📄 Export to PDF
Generate professional audit reports including:
- Reaction configuration and parameters
- Sustainability metrics and grades
- Environmental impact analysis
- AI-powered recommendations

### 🔬 Scientific Constraints & Validation

The application implements rigorous scientific validation:

#### 1. **Mass Balance Check (Conservation of Mass)**
- Validates that total output mass doesn't exceed theoretical input mass
- Provides warnings when mass balance appears inconsistent
- Ensures compliance with the Law of Conservation of Mass

#### 2. **Molecular Weight Rationality**
- Prevents calculations when Product MW > Reactant MW
- Enforces fundamental atom economy constraints
- Blocks invalid theoretical scenarios

#### 3. **Division-by-Zero Protection**
- Validates all input parameters before calculations
- Provides clear error messages for invalid inputs
- Ensures application stability

#### 4. **Toxicity Assessment**
- Evaluates solvent toxicity (High/Moderate/Low)
- Considers green principles in toxicity scoring
- Provides color-coded hazard warnings

## 🛠️ Tech Stack

- **Python 3.8+**: Core programming language
- **Streamlit**: Web application framework
- **Plotly**: Interactive data visualization
- **FPDF**: PDF report generation
- **NumPy/Pandas**: Data processing (optional)

## 📦 Installation Guide

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/ai-green-auditor.git
cd ai-green-auditor
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Train/refresh model artifacts (one-time or after updates)
```bash
python models/ml_model.py
```

### Step 4: Run the Streamlit frontend
```bash
streamlit run app.py
```

The application will open automatically in your default web browser at `http://localhost:8501`

### Step 5: Run API server (FastAPI, optional)
```bash
uvicorn app:API_APP --host 0.0.0.0 --port 8000 --reload
```

API base URL: `http://localhost:8000/api`
- `POST /api/predict`
- `POST /api/calculate`
- `POST /api/report` (returns PDF bytes)

## 🚀 Quick Start

1. **Enter Reaction Data**:
   - Reaction name (optional)
   - Molecular weights (Reactants and Product)
   - Mass values (Product and Waste)
   - Select solvent

2. **Select Green Principles**:
   - Expand the principles section
   - Check all applicable principles

3. **View Analytics**:
   - Review the 2×2 analytics grid
   - Check sustainability grade and score
   - Examine impact metrics

4. **Export Report**:
   - Click "Download Audit Report (PDF)"
   - Save for documentation or presentation

## 📁 Project Structure

```text
Green_Synth_AI/
├── app.py                  # Thin entrypoint: Streamlit + FastAPI wiring
├── requirements.txt
├── data/                   # Generated CSV datasets
├── models/                 # ML training/inference modules + model artifacts
├── services/               # Business/domain services (chemistry, impact, NLP, etc.)
├── routes/                 # FastAPI routes + optional Flask app
└── frontend/               # Streamlit UI composition (charts/components/theme)
```

## 🔌 End-to-End Module Wiring

- `app.py` initializes:
  - `frontend.app_ui.render_main_page()` for Streamlit
  - `API_APP` with `routes.api.api_router` mounted under `/api`
- `routes/api.py` connects API requests to:
  - `models/ml_model.py` for ML predictions
  - `services/pdf_report.py` for PDF export
- `frontend/app_ui.py` connects UI interactions to:
  - `services/chemistry.py`, `services/recommender.py`, `services/comparator.py`, `services/nlp_parser.py`

## 🚀 Deployment Options

### A) Streamlit deployment
1. Ensure `requirements.txt` is installed.
2. Ensure model artifact exists (`python models/ml_model.py`).
3. Start:
   ```bash
   streamlit run app.py
   ```
4. Deploy on Streamlit Cloud or any VM/container by exposing port `8501`.

### B) FastAPI deployment (recommended API)
1. Start with Uvicorn:
   ```bash
   uvicorn app:API_APP --host 0.0.0.0 --port 8000
   ```
2. Put behind Nginx/Caddy in production.

### C) Flask deployment (optional compatibility)
This project includes `routes/flask_app.py` with equivalent endpoints.
```bash
python routes/flask_app.py
```
or with gunicorn:
```bash
gunicorn -w 2 -b 0.0.0.0:5000 "routes.flask_app:FLASK_APP"
```

## 🎨 Visual Theme

- **Background**: Dark Blue (#0a1628) for professional data visualization
- **Primary Accent**: Scientific Cyan (#00e5ff) for headings and highlights
- **Success Indicators**: Muted Green (#66ff99) for positive metrics
- **Warning/Error**: Soft Red (#ff6666) for alerts and hazards
- **Grade Badges**: Dynamic glowing effects (Green/Amber/Red)

## 🧪 Example Use Cases

### Academic Research
- Evaluate experimental reaction sustainability
- Compare different synthetic routes
- Generate reports for publications

### Industrial Applications
- Process optimization and green chemistry audits
- Regulatory compliance documentation
- Environmental impact assessments

### Educational Purposes
- Teaching green chemistry principles
- Student lab report generation
- Sustainability awareness training

## 🔒 Scientific Validation

All calculations are validated against:
- ✅ Law of Conservation of Mass
- ✅ Atom Economy Constraints
- ✅ Stoichiometric Principles
- ✅ Toxicity Guidelines

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

## 🙏 Acknowledgments

- Green Chemistry principles based on Anastas and Warner's 12 Principles
- Inspired by sustainable chemistry initiatives worldwide
- Built with modern web technologies for accessibility

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: support@example.com
- Documentation: [Wiki](https://github.com/yourusername/ai-green-auditor/wiki)

## 🔄 Version History

- **v1.0.0** (2024): Initial release
  - Core analytics dashboard
  - 12 Green Chemistry principles
  - PDF export functionality
  - Scientific validation system
  - Toxicity assessment

---

**Made with 💚 for a sustainable future**
