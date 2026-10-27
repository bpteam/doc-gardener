# Agent hooks (optional)

Hooks belong to the coding agent, not to this skill. Installing the skill installs no hooks. Use a hook only when the team wants a mechanical reminder at the end of a task; it complements, not replaces, the rule in [`assets/AGENTS_SNIPPET.md`](../assets/AGENTS_SNIPPET.md).

## Claude Code: block stopping while changed docs have broken references

`.claude/settings.json` in the target repository (assumes the script was vendored to `tools/docgraph.py`):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/tools/docgraph-stop-hook.py\""
          }
        ]
      }
    ]
  }
}
```

`tools/docgraph-stop-hook.py`:

```python
#!/usr/bin/env python3
"""Stop hook: exit 2 (block, message to the agent) if changes since HEAD broke doc references."""
import json, os, subprocess, sys

event = json.load(sys.stdin)
if event.get('stop_hook_active'):  # already blocked once in this stop cycle; do not loop
    sys.exit(0)
root = os.environ.get('CLAUDE_PROJECT_DIR', '.')
script = os.path.join(root, 'tools', 'docgraph.py')
check = subprocess.run([sys.executable, script, 'check', '--root', root, '--changed', 'HEAD'],
                       capture_output=True, text=True)
impact = subprocess.run([sys.executable, script, 'impact', '--root', root, '--base', 'HEAD', '--json'],
                        capture_output=True, text=True)
routed = json.loads(impact.stdout or '{}').get('referencing_docs', {}) if impact.returncode == 0 else {}
messages = []
if check.returncode == 1:
    messages.append('Documentation references broken by this change:\n' + check.stdout)
if routed:
    messages.append('Docs that reference changed code; confirm they are still accurate (doc-gardener SYNC) '
                    'or state why no update is needed:\n' + json.dumps(routed, indent=2))
if messages:
    print('\n\n'.join(messages), file=sys.stderr)
    sys.exit(2)
```

Exit code 2 from a Stop hook keeps the agent working and feeds stderr back to it; `stop_hook_active` prevents an endless loop when the agent decides no change is needed.

## Other agents

Codex, Cursor and others have different (or no) lifecycle hooks. The portable mechanisms are the activation rule in the project's agent instructions and the CI check ([`CI_EXAMPLE.md`](CI_EXAMPLE.md)).
