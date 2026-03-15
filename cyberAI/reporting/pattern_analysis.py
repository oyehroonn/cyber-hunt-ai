"""Step 20.5: Pattern Analysis."""
from cyberAI.models import VerifiedFinding, PatternCluster

def cluster_by_pattern(findings: list[VerifiedFinding]) -> list[PatternCluster]:
    clusters = {}
    for f in findings:
        key = f.root_cause or f.category.value
        if key not in clusters:
            clusters[key] = PatternCluster(pattern_name=key, root_cause=key, recommended_fix=f"Fix {key}", fix_complexity="medium")
        clusters[key].finding_ids.append(f.id)
    return list(clusters.values())
