"""
Module for analyzing spending patterns and trends.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from .types import AnalysisPeriod


class SpendingAnalyzer:
    """Analyzes spending patterns and trends."""

    def analyze_by_category(
        self,
        transactions: pd.DataFrame,
        period: Optional[AnalysisPeriod] = None
    ) -> Dict[str, Any]:
        """
        Analyze spending by category.

        Args:
            transactions: DataFrame of transactions
            period: Optional time period for analysis

        Returns:
            Dictionary containing category-wise analysis including:
            - Total spending by category
            - Monthly trends
            - Percentage of total spending
            - Growth rates
        """
        if period:
            mask = (transactions['date'] >= period.start_date) & \
                   (transactions['date'] <= period.end_date)
            transactions = transactions[mask]

        # Ensure date is datetime
        transactions['date'] = pd.to_datetime(transactions['date'])

        # Calculate total spending by category
        category_totals = transactions.groupby('category_id')['amount'].sum()

        # Calculate monthly spending by category
        monthly_spending = transactions.groupby([
            pd.Grouper(key='date', freq='M'),
            'category_id'
        ])['amount'].sum().unstack(fill_value=0)

        # Calculate growth rates (comparing last month to average of previous months)
        growth_rates = {}
        if len(monthly_spending) > 1:
            last_month = monthly_spending.iloc[-1]
            prev_months_avg = monthly_spending.iloc[:-1].mean()
            growth_rates = ((last_month - prev_months_avg) / prev_months_avg * 100).to_dict()

        # Calculate percentage of total spending
        total_spending = category_totals.sum()
        spending_percentages = (category_totals / total_spending * 100).to_dict()

        # Calculate seasonal patterns (if enough data)
        seasonal_patterns = {}
        if len(monthly_spending) >= 12:
            monthly_avg = monthly_spending.groupby(
                monthly_spending.index.month
            ).mean()
            seasonal_patterns = monthly_avg.to_dict()

        return {
            'total_by_category': category_totals.to_dict(),
            'monthly_trends': monthly_spending.to_dict(),
            'growth_rates': growth_rates,
            'spending_percentages': spending_percentages,
            'seasonal_patterns': seasonal_patterns
        }

    def year_over_year_comparison(
        self,
        transactions: pd.DataFrame,
        categories: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Compare spending patterns across years.

        Args:
            transactions: DataFrame of transactions
            categories: Optional list of category IDs to analyze

        Returns:
            Dictionary containing year-over-year comparisons
        """
        # Ensure date is datetime
        transactions['date'] = pd.to_datetime(transactions['date'])

        # Filter categories if specified
        if categories:
            transactions = transactions[transactions['category_id'].isin(categories)]

        # Group by year and category
        yearly_spending = transactions.groupby([
            transactions['date'].dt.year,
            'category_id'
        ])['amount'].sum().unstack(fill_value=0)

        # Calculate year-over-year growth
        yoy_growth = {}
        if len(yearly_spending) > 1:
            yoy_growth = (
                (yearly_spending.iloc[-1] - yearly_spending.iloc[-2]) /
                yearly_spending.iloc[-2] * 100
            ).to_dict()

        # Calculate average spending by month for each year
        monthly_avg_by_year = transactions.groupby([
            transactions['date'].dt.year,
            transactions['date'].dt.month,
            'category_id'
        ])['amount'].mean().unstack(fill_value=0)

        return {
            'yearly_totals': yearly_spending.to_dict(),
            'yoy_growth': yoy_growth,
            'monthly_averages': monthly_avg_by_year.to_dict()
        }

    def identify_spending_anomalies(
        self,
        transactions: pd.DataFrame,
        threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Identify unusual spending patterns using statistical methods.

        Args:
            transactions: DataFrame of transactions
            threshold: Standard deviation threshold for anomalies (z-score)

        Returns:
            List of identified anomalies with details
        """
        anomalies = []

        # Ensure date is datetime
        transactions['date'] = pd.to_datetime(transactions['date'])

        # Group transactions by category
        for category_id in transactions['category_id'].unique():
            cat_transactions = transactions[
                transactions['category_id'] == category_id
            ]

            # Calculate z-scores for amounts
            mean_amount = cat_transactions['amount'].mean()
            std_amount = cat_transactions['amount'].std()

            if std_amount > 0:  # Avoid division by zero
                z_scores = (cat_transactions['amount'] - mean_amount) / std_amount

                # Find transactions with high z-scores
                anomalous_txns = cat_transactions[abs(z_scores) > threshold]

                for _, txn in anomalous_txns.iterrows():
                    anomalies.append({
                        'category_id': category_id,
                        'transaction_id': txn.name,
                        'amount': txn['amount'],
                        'date': txn['date'].strftime('%Y-%m-%d'),
                        'z_score': z_scores[txn.name],
                        'avg_amount': mean_amount,
                        'std_amount': std_amount
                    })

            # Check for unusual monthly patterns using IQR
            monthly_totals = cat_transactions.groupby(
                pd.Grouper(key='date', freq='M')
            )['amount'].sum()

            Q1 = monthly_totals.quantile(0.25)
            Q3 = monthly_totals.quantile(0.75)
            IQR = Q3 - Q1

            # Find months with unusual total spending
            unusual_months = monthly_totals[
                (monthly_totals < (Q1 - 1.5 * IQR)) |
                (monthly_totals > (Q3 + 1.5 * IQR))
            ]

            for date, amount in unusual_months.items():
                anomalies.append({
                    'category_id': category_id,
                    'date': date.strftime('%Y-%m'),
                    'amount': amount,
                    'type': 'monthly_anomaly',
                    'expected_range': {
                        'min': Q1 - 1.5 * IQR,
                        'max': Q3 + 1.5 * IQR
                    }
                })

        return anomalies
