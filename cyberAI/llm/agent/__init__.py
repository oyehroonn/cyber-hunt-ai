"""
Closed-loop assessment agent: tool-calling LLM + executor + persistent memory.

See docs/AGENT_LOOP_ARCHITECTURE.md.
"""

from cyberAI.llm.agent.loop import run_agent_loop

__all__ = ["run_agent_loop"]
