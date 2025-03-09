"""
Module for analyzing budget performance and generating recommendations.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from .types import AnalysisPeriod


class BudgetAnalyzer:
    """Analyzes budget performance and generates recommendations."""

    def analyze_budget_performance(
        self,
        transactions: pd.DataFrame,
        budgets: Dict[int, float],
        period: Optional[AnalysisPeriod] = None
    ) -> Dict[str, Any]:
        """
        Analyze performance against budget targets.

        Args:
            transactions: DataFrame of transactions
            budgets: Dictionary of category ID to budget amount
            period: Optional time period for analysis

        Returns:
            Dictionary containing budget performance metrics including:
            - Actual vs budget comparison
            - Percentage of budget used
            - Trend analysis
            - Projected overspend/underspend
        """
        if period:
            mask = (transactions["date"] >= period.start_date) & \
                   (transactions["date"] <= period.end_date)
            transactions = transactions[mask]

        # Ensure date is datetime
        transactions["date"] = pd.to_datetime(transactions["date"])

        results = {}

        # Calculate actual spending by category
        actual_spending = transactions.groupby("category_id")["amount"].sum()

        # Compare with budgets
        for category_id, budget in budgets.items():
            actual = actual_spending.get(category_id, 0)

            # Calculate basic metrics
            percentage_used = (actual / budget) * 100 if budget > 0 else 0
            variance = actual - budget

            # Calculate monthly trend
            monthly_spending = transactions[
                transactions["category_id"] == category_id
            ].groupby(pd.Grouper(key="date", freq="M"))["amount"].sum()

            # Project end-of-period spending based on current trend
            if len(monthly_spending) >= 2:
                avg_monthly = monthly_spending.mean()
                remaining_months = 12 - len(monthly_spending)
                projected_total = actual + (avg_monthly * remaining_months)
                projected_variance = projected_total - budget
            else:
                projected_total = actual
                projected_variance = variance

            results[category_id] = {
                "budget": budget,
                "actual": actual,
                "percentage_used": percentage_used,
                "variance": variance,
                "monthly_trend": monthly_spending.to_dict(),
                "projected_total": projected_total,
                "projected_variance": projected_variance,
                "status": "over_budget" if variance > 0 else "under_budget"
            }

        return results

    def generate_budget_recommendations(
        self,
        transactions: pd.DataFrame,
        current_budgets: Dict[int, float]
    ) -> List[Dict[str, Any]]:
        """
        Generate budget adjustment recommendations based on:
        - Historical spending patterns
        - Seasonal variations
        - Current performance
        - Spending trends

        Args:
            transactions: DataFrame of transactions
            current_budgets: Current budget allocations

        Returns:
            List of budget recommendations
        """
        recommendations = []

        # Ensure date is datetime
        transactions["date"] = pd.to_datetime(transactions["date"])

        for category_id, current_budget in current_budgets.items():
            cat_transactions = transactions[
                transactions["category_id"] == category_id
            ]

            if len(cat_transactions) == 0:
                continue

            # Calculate historical monthly averages
            monthly_avg = cat_transactions.groupby(
                pd.Grouper(key="date", freq="M")
            )["amount"].mean()

            # Calculate seasonal patterns
            seasonal_avg = cat_transactions.groupby(
                cat_transactions["date"].dt.month
            )["amount"].mean()

            # Calculate recent trend (last 3 months)
            recent_months = cat_transactions.sort_values("date").tail(90)
            recent_avg = recent_months["amount"].mean()

            # Generate recommendations based on patterns
            recommended_budget = recent_avg * 1.1  # Add 10% buffer

            if len(seasonal_avg) >= 12:
                # Adjust for upcoming seasonal changes
                next_month = (pd.Timestamp.now().month % 12) + 1
                seasonal_factor = seasonal_avg[next_month] / seasonal_avg.mean()
                recommended_budget *= seasonal_factor

            if abs(recommended_budget - current_budget) / current_budget > 0.1:
                recommendations.append({
                    "category_id": category_id,
                    "current_budget": current_budget,
                    "recommended_budget": round(recommended_budget, 2),
                    "change_percentage": round(
                        (recommended_budget - current_budget) / current_budget * 100,
                        1
                    ),
                    "reason": [
                        f"Historical monthly average: ${round(monthly_avg.mean(), 2)}",
                        f"Recent 3-month average: ${round(recent_avg, 2)}",
                        "Seasonal adjustment applied" if len(seasonal_avg) >= 12 else None
                    ],
                    "confidence": "high" if len(cat_transactions) > 100 else "medium"
                })

        return sorted(
            recommendations,
            key=lambda x: abs(x["change_percentage"]),
            reverse=True
        )
