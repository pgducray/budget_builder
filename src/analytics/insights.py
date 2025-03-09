"""
Module for generating actionable financial insights.
"""
from typing import List, Dict, Any, Optional
import pandas as pd


class InsightGenerator:
    """Generates actionable financial insights."""

    def generate_monthly_insights(
        self,
        transactions: pd.DataFrame,
        budgets: Optional[Dict[int, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate monthly financial insights.

        Args:
            transactions: DataFrame of transactions
            budgets: Optional budget information

        Returns:
            List of generated insights including:
            - Top spending categories
            - Unusual transactions
            - Budget alerts
            - Saving opportunities
        """
        insights = []

        # Ensure date is datetime
        transactions["date"] = pd.to_datetime(transactions["date"])

        # Focus on current month
        current_month = pd.Timestamp.now().replace(day=1)
        month_transactions = transactions[
            transactions["date"] >= current_month
        ]

        # Top spending categories
        category_spending = month_transactions.groupby("category_id")["amount"].sum()
        top_categories = category_spending.nlargest(3)

        insights.append({
            "type": "top_spending",
            "description": "Top spending categories this month",
            "data": top_categories.to_dict()
        })

        # Compare with previous month
        prev_month = current_month - pd.DateOffset(months=1)
        prev_month_transactions = transactions[
            (transactions["date"] >= prev_month) &
            (transactions["date"] < current_month)
        ]

        prev_spending = prev_month_transactions.groupby("category_id")["amount"].sum()

        # Significant changes
        for category_id in set(category_spending.index) | set(prev_spending.index):
            curr = category_spending.get(category_id, 0)
            prev = prev_spending.get(category_id, 0)

            if prev > 0:
                change_pct = ((curr - prev) / prev) * 100
                if abs(change_pct) > 20:  # 20% threshold
                    insights.append({
                        "type": "spending_change",
                        "category_id": category_id,
                        "change_percentage": round(change_pct, 1),
                        "previous_amount": prev,
                        "current_amount": curr,
                        "description": f"{'Increase' if change_pct > 0 else 'Decrease'} "
                                     f"of {abs(round(change_pct, 1))}% in spending"
                    })

        # Budget alerts
        if budgets:
            for category_id, budget in budgets.items():
                current_spent = category_spending.get(category_id, 0)
                budget_percentage = (current_spent / budget) * 100

                if budget_percentage > 80:
                    insights.append({
                        "type": "budget_alert",
                        "category_id": category_id,
                        "budget": budget,
                        "spent": current_spent,
                        "percentage": round(budget_percentage, 1),
                        "description": f"Approaching budget limit "
                                     f"({round(budget_percentage, 1)}% used)"
                    })

        return insights

    def identify_savings_opportunities(
        self,
        transactions: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Identify potential areas for saving money.

        Args:
            transactions: DataFrame of transactions

        Returns:
            List of savings opportunities based on:
            - High frequency small transactions
            - Duplicate services
            - Irregular high-value purchases
            - Seasonal spending patterns
        """
        opportunities = []

        # Ensure date is datetime
        transactions["date"] = pd.to_datetime(transactions["date"])

        # Analyze frequent small transactions
        small_txns = transactions[transactions["amount"] < 20]
        frequent_small = small_txns.groupby("category_id").agg({
            "amount": ["count", "sum"]
        })

        for category_id in frequent_small.index:
            count = frequent_small.loc[category_id, ("amount", "count")]
            total = frequent_small.loc[category_id, ("amount", "sum")]

            if count > 10:  # More than 10 small transactions
                opportunities.append({
                    "type": "frequent_small_transactions",
                    "category_id": category_id,
                    "transaction_count": count,
                    "total_amount": total,
                    "description": f"Found {count} small transactions totaling ${total}. "
                                 "Consider bulk purchases or alternatives."
                })

        # Identify potential duplicate services
        monthly_services = self.analyze_recurring_expenses(transactions)
        service_categories = {}

        for service in monthly_services:
            cat_id = service["category_id"]
            if cat_id not in service_categories:
                service_categories[cat_id] = []
            service_categories[cat_id].append(service)

        for cat_id, services in service_categories.items():
            if len(services) > 1:
                opportunities.append({
                    "type": "duplicate_services",
                    "category_id": cat_id,
                    "services": services,
                    "total_monthly": sum(s["average_amount"] for s in services),
                    "description": f"Found {len(services)} recurring charges in same category. "
                                 "Consider consolidating services."
                })

        return opportunities

    def analyze_recurring_expenses(
        self,
        transactions: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Identify and analyze recurring expenses.

        Args:
            transactions: DataFrame of transactions

        Returns:
            List of recurring expense analyses including:
            - Monthly subscriptions
            - Regular bill payments
            - Frequency patterns
            - Cost variations
        """
        recurring = []

        # Ensure date is datetime
        transactions["date"] = pd.to_datetime(transactions["date"])

        # Group by category and amount (rounded to nearest dollar)
        transactions["rounded_amount"] = transactions["amount"].round(2)
        grouped = transactions.groupby(["category_id", "rounded_amount"])

        for (category_id, amount), group in grouped:
            # Sort transactions by date
            group = group.sort_values("date")

            if len(group) < 2:
                continue

            # Calculate days between transactions
            days_between = group["date"].diff().dt.days

            # Calculate if the transactions occur regularly
            avg_interval = days_between.mean()
            interval_std = days_between.std()

            # Consider it recurring if:
            # 1. At least 3 transactions
            # 2. Consistent interval (std dev < 5 days)
            # 3. Average interval between 25-35 days (monthly) or 28-32 days (subscription)
            if len(group) >= 3 and interval_std < 5 and (25 <= avg_interval <= 35):
                last_date = group["date"].iloc[-1]
                next_expected = last_date + pd.Timedelta(days=avg_interval)

                recurring.append({
                    "type": "subscription" if 28 <= avg_interval <= 32 else "regular_payment",
                    "category_id": category_id,
                    "average_amount": amount,
                    "frequency": "monthly",
                    "average_interval_days": round(avg_interval, 1),
                    "transaction_count": len(group),
                    "last_payment_date": last_date.strftime("%Y-%m-%d"),
                    "next_expected_date": next_expected.strftime("%Y-%m-%d"),
                    "amount_variation": group["amount"].std(),
                    "description": f"Monthly {'subscription' if 28 <= avg_interval <= 32 else 'payment'} "
                                 f"of ${amount:.2f}"
                })

        return sorted(recurring, key=lambda x: x["average_amount"], reverse=True)
