# Personal Finance Tracker Development Guide

## **Objective**

The goal of this project is to help individuals analyze their bank statements, build financial analytics, and make data-driven decisions for budgeting and managing personal finances. The tool will focus on automating transaction categorization and providing actionable insights through a lightweight and user-friendly solution.

---

## **Steps to Develop the Code**

### **1. Define Objectives and Workflow**
Break the project into manageable components:

1. **Data Cleaning and Ingestion**:  
   - Load CSV bank statements.
   - Deduplicate transactions to handle overlapping statement dates.
   - Store the data in a structured format.

2. **Transaction Categorization**:  
   - Automatically categorize transactions based on user-defined rules.
   - Build a feedback loop for the user to refine and enhance categorization logic.

3. **Year-Over-Year Comparison**:  
   - Analyze expenses by category over time.
   - Generate insights on spending trends.

4. **Budget Insights**:  
   - Suggest improvements for budgeting.
   - Highlight spending anomalies and provide goal-tracking features.

---

### **2. Tools and Libraries**

#### **Recommended Tools**:
- **Pandas**: For data manipulation (loading, cleaning, deduplication).
- **SQLite**: A lightweight database for storing transactions and rules without requiring a server.
- **Matplotlib/Plotly/Seaborn**: For visualizing trends and insights.
- **NLP/Keyword Extraction Libraries**:
  - `spaCy`, `NLTK`, or `TextBlob` for text analysis.
  - Pre-trained models (e.g., `HuggingFace Transformers`) if advanced categorization is needed.
- **Docker**: To containerize the application for deployment.

---

### **3. Implementation Steps**

#### **a. Data Cleaning and Storage**
- **Deduplication**:
  - Compare transactions based on `Transaction_ID`, `Date`, and `Amount`.
- **Storage**:
  - Use an SQLite database to:
    - Store cleaned transaction data.
    - Handle overlapping bank statement dates efficiently.
    - Enable easy queries for categorization and analytics.

---

#### **b. Transaction Categorization**

##### **Step 1: Initial Rule-Based Categorization**:
1. Define categories (e.g., "Groceries", "Fuel", "Entertainment").
2. Map keywords, vendor names, or accounts to categories:
   - Example: "Walmart" → "Groceries", "Shell" → "Fuel".
3. Create rules that match transaction descriptions with predefined keywords.

##### **Step 2: User Feedback Loop**:
1. Present uncategorized transactions to the user for manual categorization.
2. Allow users to define new rules for vendors, keywords, or accounts.
3. Store these rules in a database for future automated categorization.

##### **Step 3: Automate Matching**:
1. For new transactions, match against stored rules:
   - Vendor matches take precedence.
   - Fallback to keyword or account-based rules.
2. Alert the user to resolve ambiguous matches.

##### **Advanced Option**:
- Train an ML model using user-categorized data to handle edge cases or ambiguous descriptions.
- Use NLP to extract keywords and infer categories dynamically.

---

#### **c. Year-Over-Year Comparison**

1. Query the database for:
   - Aggregated spending per category and year.
   - Trends or spikes in specific expense areas.
2. Generate visualizations:
   - **Line Charts**: Show spending trends over time.
   - **Pie Charts**: Highlight category-wise distribution.
3. Add insights:
   - Identify categories with the highest year-over-year growth.
   - Suggest areas for spending cuts or goal adjustments.

---

#### **d. Budgeting Insights**

1. Analyze spending patterns to:
   - Highlight categories exceeding budget limits.
   - Suggest budgeting goals for each category.
2. Provide actionable insights:
   - Highlight seasonal spending patterns.
   - Identify recurring expenses and recommend optimizations.

---

### **4. Implementation Considerations**

#### **a. Matching Logic**:
- **Prioritization**:
  - Vendor Name Matches > Keyword Matches > Account Rules.
- **Customization**:
  - Allow users to override rules or assign categories for ambiguous transactions.

#### **b. Storing Rules**:
- Use a structured database (SQLite) with fields:
  - **Keyword/Vendor**: E.g., "Walmart".
  - **Category**: E.g., "Groceries".
  - **User Notes**: Additional metadata for rules.

#### **c. Conflict Resolution**:
- Resolve overlaps by:
  - Allowing users to set rule precedence.
  - Notifying users about ambiguous matches for review.

#### **d. Periodic Review**:
- Build a user-friendly review interface to:
  - Audit past categorizations.
  - Update rules and improve accuracy over time.
