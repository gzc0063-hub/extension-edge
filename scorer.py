"""
scorer.py — Efficacy ranking and best/backup selection.

Approved products are ranked by a priority-weighted lexicographic sort:
the producer's #1 weed dominates, then #2, then #3, etc.

Rating scale (from IPM-0028A):
    E = Excellent (4)
    G = Good      (3)
    F = Fair      (2)
    P = Poor      (1)
    — / blank     (0)
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

SCORE = {"E": 4, "G": 3, "F": 2, "P": 1, "—": 0, "-": 0, "": 0}
GOOD_OR_BETTER_MIN = 3   # G or higher counts as adequate control


def _rating_for(efficacy_df: pd.DataFrame, unique_id: str, weed_id: str) -> str:
    """Lookup the rating string for a (product, weed) pair. '' if absent."""
    matches = efficacy_df[
        (efficacy_df["unique_id"] == unique_id) &
        (efficacy_df["weed_id"] == weed_id)
    ]
    if matches.empty:
        return ""
    return str(matches.iloc[0]["rating"]).strip()


def rank_by_efficacy(
    approved: List[Dict[str, Any]],
    priority_weeds: List[str],
    efficacy_df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """
    Return approved products sorted best-first by tuple of efficacy scores
    across priority_weeds (in order). Each product is annotated with:
        product["_scores"]  -> tuple of int scores aligned with priority_weeds
        product["_ratings"] -> dict {weed_id: rating_letter}
    """
    enriched: List[Dict[str, Any]] = []
    for product in approved:
        ratings: Dict[str, str] = {}
        scores: List[int] = []
        for w in priority_weeds:
            r = _rating_for(efficacy_df, product["unique_id"], w)
            ratings[w] = r if r else "—"
            scores.append(SCORE.get(r, 0))
        p = dict(product)
        p["_scores"] = tuple(scores)
        p["_ratings"] = ratings
        enriched.append(p)

    # Lexicographic sort — first weed dominates, then second, etc.
    enriched.sort(key=lambda p: p["_scores"], reverse=True)
    return enriched


def covers_all_weeds(product: Dict[str, Any], min_score: int = GOOD_OR_BETTER_MIN) -> bool:
    """True iff every priority weed has score >= min_score."""
    scores = product.get("_scores", ())
    return bool(scores) and all(s >= min_score for s in scores)


def select_best(ranked: List[Dict[str, Any]]) -> Tuple[
    Optional[Dict[str, Any]],
    Optional[Dict[str, Any]],
    List[Dict[str, Any]],
]:
    """
    From a ranked list, return (best, backup, partial_options).
        best   = top product if it covers all weeds at G or better, else None
        backup = next-best with same coverage if best exists, else None
        partial_options = top 3 ranked products (only meaningful if best is None)
    """
    if not ranked:
        return None, None, []

    full_coverage = [p for p in ranked if covers_all_weeds(p)]
    if not full_coverage:
        return None, None, ranked[:3]

    best = full_coverage[0]
    backup = full_coverage[1] if len(full_coverage) > 1 else None
    return best, backup, ranked[:3]
