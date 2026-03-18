"""
ASRTS security-relevance scorer for crawl prioritisation.
Scores URLs 0.0–1.0 so high-value (api, admin, forms) are crawled first.
Rule-based by default; optional sklearn TF-IDF + logistic regression (Phase 3).
"""

import re
from typing import Optional
from urllib.parse import urlparse


# Path segments that indicate high security relevance (attack surface)
HIGH_RELEVANCE = [
    "api", "admin", "user", "users", "account", "auth", "login", "signin",
    "settings", "config", "profile", "dashboard", "upload", "download",
    "export", "import", "manage", "billing", "payment", "order", "orders",
    "cart", "checkout", "webhook", "callback", "token", "oauth",
    "graphql", "rest", "v1", "v2", "internal", "private", "secure",
]
# Medium relevance
MEDIUM_RELEVANCE = [
    "form", "search", "edit", "create", "new", "delete", "update",
    "preferences", "notifications", "invite", "team", "org", "tenant",
]


def score_url_security_relevance(url: str) -> float:
    """
    Return a score in [0.0, 1.0] for crawl priority.
    Higher = more likely to expose attack surface (APIs, auth, admin).
    """
    try:
        parsed = urlparse(url)
        path = (parsed.path or "").lower()
        # Strip numeric/ID segments for pattern matching
        path_for_match = re.sub(r"/\d+", "", path)
        path_for_match = re.sub(r"/[0-9a-f-]{36}", "", path_for_match)
        score = 0.0
        for seg in HIGH_RELEVANCE:
            if seg in path_for_match or f"/{seg}" in path or path.startswith(seg + "/") or path == seg:
                score += 0.15
        for seg in MEDIUM_RELEVANCE:
            if seg in path_for_match or f"/{seg}" in path or path.startswith(seg + "/") or path == seg:
                score += 0.06
        # Cap at 1.0
        return min(1.0, score)
    except Exception:
        return 0.0


def path_template_for_novelty(url: str) -> str:
    """Replace numeric/UUID path segments with {id} for novelty shape."""
    try:
        parsed = urlparse(url)
        path = parsed.path or "/"
        path = re.sub(r"/\d+", "/{id}", path)
        path = re.sub(r"/[0-9a-fA-F-]{36}", "/{id}", path)
        path = re.sub(r"/[0-9a-fA-F]{32}", "/{id}", path)
        return f"{parsed.netloc}{path}"
    except Exception:
        return url


class SecurityRelevanceScorer:
    """
    Optional ML-backed scorer (sklearn TF-IDF + logistic regression).
    When fit() has not been called or sklearn is missing, score() uses rule-based score_url_security_relevance.
    """

    def __init__(self) -> None:
        self._vect = None
        self._clf = None

    def fit(self, urls: list[str], labels: Optional[list[float]] = None) -> bool:
        """
        Train on URLs. If labels is None, derive from rule-based: 1.0 if score_url_security_relevance > 0.3 else 0.0.
        Returns True if sklearn was available and model was fitted.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
        except ImportError:
            return False
        if not urls:
            return False
        if labels is None:
            labels = [1.0 if score_url_security_relevance(u) > 0.3 else 0.0 for u in urls]
        self._vect = TfidfVectorizer(max_features=500, ngram_range=(1, 2), sublinear_tf=True)
        X = self._vect.fit_transform(urls)
        self._clf = LogisticRegression(max_iter=500, random_state=42)
        self._clf.fit(X, labels)
        return True

    def score(self, url: str) -> float:
        """Return 0.0–1.0; uses ML when fitted, else rule-based."""
        if self._vect is not None and self._clf is not None:
            try:
                X = self._vect.transform([url])
                return float(self._clf.predict_proba(X)[0, 1])
            except Exception:
                pass
        return score_url_security_relevance(url)
