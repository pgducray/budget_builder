# Personal Finance Tracker

A Python-based tool for analyzing bank statements, automating transaction categorization, and providing financial insights.

## Project Structure

```
budget_builder/
├── src/                    # Source code
│   ├── data_processing/    # Data cleaning and transformation
│   ├── categorization/     # Transaction categorization logic
│   ├── analytics/          # Financial analysis and insights
│   ├── database/          # Database operations
│   └── utils/             # Utility functions
├── tests/                  # Test files mirroring src/ structure
├── data/                   # Data directory
│   ├── raw/               # Original bank statements
│   └── processed/         # Cleaned and processed data
├── config/                # Configuration files
├── notebooks/             # Jupyter notebooks for exploration
├── docker/                # Docker configuration
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

## Setup Instructions

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update variables as needed

## Development Workflow

1. Data Processing:
   - Place bank statements in `data/raw/`
   - Run data cleaning scripts
   - Processed data saved to `data/processed/`

2. Transaction Categorization:
   - Define rules in configuration
   - Process transactions
   - Review and update categorizations

3. Analysis:
   - Generate insights and visualizations
   - Export reports

## Testing

Run tests using pytest:
```bash
pytest tests/
```

## Docker Support

Build and run using Docker:
```bash
docker build -t finance-tracker .
docker run finance-tracker
