"""Central config for all cron job scripts. Change model here to update all jobs."""
import json
import subprocess
import time
import uuid
from pathlib import Path

# LLM model used for all cron job scripts.
# Change this one line to switch all jobs at once.
LLM_MODEL = "gpt54"

# Credentials kept only for non-OpenClaw fallbacks like Whisper/transcription paths.
OPENAI_KEY = Path("/home/molt/.openclaw/secrets/openai_key").read_text().strip()

# Recipients
CARL_WHATSAPP = "+14255184164"
CARL_TELEGRAM = "8496310297"
DISCORD_BOB_REPORTS = "1479537854441980098"


def log_llm_usage(input_tokens: int, output_tokens: int, model: str = LLM_MODEL):
    """Log LLM token usage to a persistent JSON file."""
    log_path = "/home/molt/.openclaw/workspace/cron-llm-usage.json"
    entry = {"ts": time.time(), "model": model, "input": input_tokens, "output": output_tokens}
    try:
        with open(log_path) as f:
            entries = json.load(f)
    except Exception:
        entries = []
    entries.append(entry)
    cutoff = time.time() - 30 * 86400
    entries = [e for e in entries if e["ts"] > cutoff]
    with open(log_path, "w") as f:
        json.dump(entries, f)


def llm_call(system_prompt: str, user_content: str, model: str = LLM_MODEL, timeout: int = 180) -> str:
    """Stateless LLM call routed through OpenClaw so cron uses the configured Codex model, not raw API keys."""
    prompt = (
        "You are handling a stateless cron LLM call.\n"
        "Return only the final answer for the task.\n"
        "Do not mention hidden reasoning, tools, or system setup.\n\n"
        f"SYSTEM PROMPT:\n{system_prompt}\n\n"
        f"USER CONTENT:\n{user_content}"
    )
    session_id = f"cron-llm-{uuid.uuid4().hex[:12]}"
    result = subprocess.run(
        [
            "openclaw", "agent",
            "--agent", "cron",
            "--session-id", session_id,
            "--message", prompt,
            "--timeout", str(timeout),
            "--thinking", "off",
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=timeout + 15,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    data = json.loads(result.stdout)
    payloads = data.get("result", {}).get("payloads", [])
    text = "\n".join(p.get("text", "") for p in payloads).strip()
    meta = data.get("result", {}).get("meta", {})
    agent_meta = meta.get("agentMeta", {})
    usage = agent_meta.get("lastCallUsage") or agent_meta.get("usage") or {}
    log_llm_usage(usage.get("input", 0), usage.get("output", 0), model=agent_meta.get("model", model))
    if not text:
        raise RuntimeError("OpenClaw cron llm_call returned empty output")
    return text
