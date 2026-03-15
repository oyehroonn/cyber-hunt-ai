"""Step 20.10: Learning Loop."""
from cyberAI.config import get_config
from cyberAI.models import LearningLoop, LearningLoopEntry, VerifiedFinding
from cyberAI.utils.helpers import atomic_write_json, load_json

def update_learning_loop(findings: list[VerifiedFinding]) -> LearningLoop:
    config = get_config()
    loop_path = config.get_output_path("learning_loop.json")
    
    existing = load_json(loop_path)
    loop = LearningLoop(**existing) if existing else LearningLoop()
    
    for f in findings:
        entry = LearningLoopEntry(
            bug_class=f.category.value,
            endpoint_pattern=f.asset,
            success_rate=f.reliability_score / 100,
        )
        loop.entries.append(entry)
        loop.high_signal_endpoints.append(f.asset)
    
    atomic_write_json(loop_path, loop.model_dump())
    return loop
