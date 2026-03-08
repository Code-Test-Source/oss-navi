"""Apriori pattern mining for recommendation associations."""

import uuid
from collections import defaultdict
from typing import TYPE_CHECKING

from pydantic import BaseModel

from oss_navi.models.recommendation import RecommendationPattern
from oss_navi.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    pass


class TransactionDatabase(BaseModel):
    """Database of transactions for pattern mining."""

    transactions: list[set[str]] = []

    def add_transaction(self, items: set[str]) -> None:
        """Add a transaction (set of items)."""
        self.transactions.append(items)

    def clear(self) -> None:
        """Clear all transactions."""
        self.transactions = []


def find_frequent_itemsets(
    transactions: list[set[str]],
    min_support: float = 0.1,
    max_length: int = 3,
) -> dict[frozenset[str], int]:
    """Find frequent itemsets using Apriori algorithm.

    Args:
        transactions: List of item sets (transactions)
        min_support: Minimum support threshold (0.0 to 1.0)
        max_length: Maximum itemset length to consider

    Returns:
        Dictionary mapping itemsets to their support counts
    """
    if not transactions:
        return {}

    num_transactions = len(transactions)
    min_count = int(min_support * num_transactions)

    # Count single items
    item_counts: dict[str, int] = defaultdict(int)
    for transaction in transactions:
        for item in transaction:
            item_counts[item] += 1

    # Filter by minimum support
    frequent_items = {
        item for item, count in item_counts.items() if count >= min_count
    }

    # Initialize with 1-itemsets
    frequent_itemsets: dict[frozenset[str], int] = {}
    current_itemsets: list[frozenset[str]] = [
        frozenset([item]) for item in frequent_items
    ]

    # Count current itemsets
    for itemset in current_itemsets:
        count = sum(1 for t in transactions if itemset.issubset(t))
        if count >= min_count:
            frequent_itemsets[itemset] = count

    # Generate larger itemsets
    length = 2
    while current_itemsets and length <= max_length:
        # Generate candidate itemsets
        candidates = _generate_candidates(current_itemsets, length)

        # Count candidates
        next_itemsets = []
        for candidate in candidates:
            count = sum(1 for t in transactions if candidate.issubset(t))
            if count >= min_count:
                frequent_itemsets[candidate] = count
                next_itemsets.append(candidate)

        current_itemsets = next_itemsets
        length += 1

    return frequent_itemsets


def _generate_candidates(
    itemsets: list[frozenset[str]],
    length: int,
) -> list[frozenset[str]]:
    """Generate candidate itemsets of given length.

    Args:
        itemsets: Current frequent itemsets
        length: Target length for new itemsets

    Returns:
        List of candidate itemsets
    """
    candidates = set()
    itemsets_list = list(itemsets)

    for i, itemset1 in enumerate(itemsets_list):
        for itemset2 in itemsets_list[i + 1 :]:
            # Join itemsets that differ by one item
            union = itemset1 | itemset2
            if len(union) == length:
                candidates.add(union)

    return list(candidates)


def generate_association_rules(
    frequent_itemsets: dict[frozenset[str], int],
    transactions: list[set[str]],
    min_confidence: float = 0.5,
) -> list[RecommendationPattern]:
    """Generate association rules from frequent itemsets.

    Args:
        frequent_itemsets: Dictionary of itemsets and their support counts
        transactions: Original transaction database
        min_confidence: Minimum confidence threshold (0.0 to 1.0)

    Returns:
        List of RecommendationPattern objects
    """
    num_transactions = len(transactions)
    patterns = []

    for itemset, support_count in frequent_itemsets.items():
        if len(itemset) < 2:
            continue

        # Generate all possible rules from this itemset
        items = list(itemset)

        for i in range(1, len(items)):
            # Antecedent is first i items, consequent is rest
            # This is a simplified approach - full Apriori considers all subsets
            for antecedent in _get_subsets(set(items), i):
                consequent = itemset - antecedent

                if not consequent:
                    continue

                # Calculate confidence
                antecedent_count = sum(
                    1 for t in transactions if antecedent.issubset(t)
                )
                if antecedent_count == 0:
                    continue

                confidence = support_count / antecedent_count

                if confidence >= min_confidence:
                    pattern = RecommendationPattern(
                        pattern_id=f"pattern-{uuid.uuid4().hex[:8]}",
                        antecedent=list(antecedent),
                        consequent=list(consequent),
                        support=support_count / num_transactions,
                        confidence=confidence,
                        algorithm="apriori",
                        created_at=utc_now(),
                    )
                    patterns.append(pattern)

    # Sort by confidence (highest first)
    patterns.sort(key=lambda p: p.confidence, reverse=True)
    return patterns


def _get_subsets(items: set[str], size: int) -> list[frozenset[str]]:
    """Get all subsets of given size.

    Args:
        items: Set of items
        size: Target subset size

    Returns:
        List of subsets as frozensets
    """
    if size == 0:
        return [frozenset()]
    if size > len(items):
        return []

    items_list = list(items)

    def backtrack(start: int, current: list[str]) -> list[frozenset[str]]:
        if len(current) == size:
            return [frozenset(current)]
        if start >= len(items_list):
            return []

        result = []
        for i in range(start, len(items_list)):
            current.append(items_list[i])
            result.extend(backtrack(i + 1, current))
            current.pop()

        return result

    return backtrack(0, [])


class AprioriMiner:
    """Apriori pattern miner for skill-project associations."""

    def __init__(
        self,
        min_support: float = 0.05,
        min_confidence: float = 0.3,
        max_itemset_length: int = 3,
    ):
        """Initialize the Apriori miner.

        Args:
            min_support: Minimum support threshold
            min_confidence: Minimum confidence threshold
            max_itemset_length: Maximum itemset length
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.max_itemset_length = max_itemset_length
        self._patterns: list[RecommendationPattern] = []

    def mine_patterns(
        self,
        transactions: list[set[str]],
    ) -> list[RecommendationPattern]:
        """Mine association patterns from transactions.

        Args:
            transactions: List of transactions (each is a set of items)

        Returns:
            List of discovered patterns
        """
        # Find frequent itemsets
        frequent_itemsets = find_frequent_itemsets(
            transactions,
            min_support=self.min_support,
            max_length=self.max_itemset_length,
        )

        # Generate association rules
        patterns = generate_association_rules(
            frequent_itemsets,
            transactions,
            min_confidence=self.min_confidence,
        )

        self._patterns = patterns
        return patterns

    def get_recommendations_for_skills(
        self,
        skills: list[str],
        top_n: int = 5,
    ) -> list[tuple[list[str], float]]:
        """Get recommended technologies based on user's skills.

        Args:
            skills: List of user's current skills/languages
            top_n: Number of recommendations to return

        Returns:
            List of (recommended_items, confidence) tuples
        """
        skill_set = {s.lower() for s in skills}
        recommendations = []

        for pattern in self._patterns:
            antecedent_set = {a.lower() for a in pattern.antecedent}

            # Check if user has all antecedent skills
            if antecedent_set.issubset(skill_set):
                recommendations.append((pattern.consequent, pattern.confidence))

        # Sort by confidence and remove duplicates
        seen_consequents = set()
        unique_recommendations = []
        for consequent, confidence in recommendations:
            consequent_tuple = tuple(sorted(consequent))
            if consequent_tuple not in seen_consequents:
                seen_consequents.add(consequent_tuple)
                unique_recommendations.append((consequent, confidence))

        return unique_recommendations[:top_n]
