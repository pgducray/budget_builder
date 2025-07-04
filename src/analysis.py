"""
Transaction analysis and pattern suggestion utilities.
"""
from typing import List, Dict, Tuple
import pandas as pd
from collections import Counter
import re
from difflib import SequenceMatcher

def similarity_score(a: str, b: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_similar_transactions(description: str, df: pd.DataFrame, threshold: float = 0.8) -> pd.DataFrame:
    """Find transactions similar to the given description."""
    scores = df['description'].apply(lambda x: similarity_score(description, x))
    return df[scores > threshold]

def extract_common_patterns(descriptions: List[str]) -> List[Tuple[str, float]]:
    """Extract common patterns from a list of descriptions."""
    # Split descriptions into words
    words = []
    for desc in descriptions:
        words.extend(re.findall(r'\b\w+\b', desc.upper()))

    # Count word frequencies
    word_counts = Counter(words)
    total_desc = len(descriptions)

    # Calculate word significance
    patterns = []
    for word, count in word_counts.items():
        if len(word) > 2:  # Ignore very short words
            significance = count / total_desc
            if significance > 0.5:  # Word appears in more than 50% of descriptions
                patterns.append((word, significance))

    return sorted(patterns, key=lambda x: x[1], reverse=True)

def suggest_pattern(description: str, df: pd.DataFrame) -> List[Dict]:
    """Suggest patterns for a given transaction description."""
    # Find similar transactions
    similar = find_similar_transactions(description, df)

    if len(similar) < 2:
        return [{
            'pattern': f"(?i){re.escape(description)}",
            'confidence': 1.0,
            'matching': 1,
            'sample': [description]
        }]

    # Extract common patterns
    common_patterns = extract_common_patterns(similar['description'].tolist())

    suggestions = []
    for pattern, confidence in common_patterns[:3]:  # Top 3 suggestions
        # Create regex pattern
        regex = f"(?i).*{pattern}.*"
        matches = df[df['description'].str.contains(regex, case=False, regex=True)]

        suggestions.append({
            'pattern': regex,
            'confidence': confidence,
            'matching': len(matches),
            'sample': matches['description'].head().tolist()
        })

    return suggestions

def group_uncategorized(df: pd.DataFrame) -> List[Dict]:
    """Group uncategorized transactions by similarity."""
    uncategorized = df[df['Category'] == 'Uncategorized']
    if len(uncategorized) == 0:
        return []

    # Group similar transactions
    groups = []
    processed = set()

    for _, row in uncategorized.iterrows():
        if row['description'] in processed:
            continue

        similar = find_similar_transactions(row['description'], uncategorized)
        if len(similar) > 0:
            group_desc = similar['description'].tolist()
            processed.update(group_desc)

            # Get pattern suggestions for the group
            suggestions = suggest_pattern(row['description'], df)

            groups.append({
                'transactions': similar.to_dict('records'),
                'count': len(similar),
                'total_amount': similar['amount'].sum(),
                'suggestions': suggestions
            })

    return sorted(groups, key=lambda x: x['count'], reverse=True)

def analyze_pattern_effectiveness(pattern: str, df: pd.DataFrame) -> Dict:
    """Analyze how effective a pattern is at categorizing transactions."""
    matches = df[df['description'].str.contains(pattern, case=False, regex=True)]
    total_uncategorized = len(df[df['Category'] == 'Uncategorized'])

    return {
        'matching_transactions': len(matches),
        'unique_descriptions': len(matches['description'].unique()),
        'total_amount': matches['amount'].sum(),
        'impact_on_uncategorized': len(matches[matches['Category'] == 'Uncategorized']) / total_uncategorized if total_uncategorized > 0 else 0,
        'sample_matches': matches['description'].head().tolist()
    }
