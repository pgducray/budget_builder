Key features to implement:

Rule Priority System: Higher priority rules are checked first
Pattern Matching Types:
Simple substring matching (e.g., "NETFLIX" → Entertainment)
Regex patterns (e.g., "^AMZN.*" → Shopping)
Amount-based rules (e.g., amount > 1000 → Large Purchases)
Rule Management:
Store rules in database with CRUD operations
Allow rule import/export via JSON
Support rule testing against sample transactions
Vendor Normalization:
Remove common suffixes (INC, LTD, LLC)
Handle common abbreviations
Clean special characters
Analytics Strategy (src/analytics/analyzer.py): The existing structure provides a good foundation. Here's how to implement the key features:
SpendingAnalyzer:

Category Analysis:
Monthly/yearly spending by category
Category growth trends
Percentage of total spending
Seasonal patterns
Anomaly Detection:
Statistical methods (z-score, IQR)
Category-specific thresholds
Historical comparison
BudgetAnalyzer:

Budget Performance:
Category-wise budget vs actual
Trend analysis and forecasting
Over/under spending alerts
Recommendations:
Based on historical patterns
Seasonal adjustments
Peer comparison (optional)
InsightGenerator:

Monthly Insights:
Top spending categories
Unusual transactions
Budget alerts
Saving opportunities
Recurring Expenses:
Pattern detection
Subscription tracking
Cost optimization suggestions
Visualization Approach:

Use Plotly/Dash for interactive visualizations:
Category pie charts
Spending trend lines
Budget progress bars
Anomaly highlight points
Dashboard Sections:
Overview (total spending, savings rate)
Category Deep-dive
Budget Tracking
Insights & Recommendations
The system should be modular and extensible, allowing new analysis types and visualizations to be added easily. Data should be cached appropriately to improve performance, and all analysis should be configurable through parameters (e.g., analysis periods, thresholds).
