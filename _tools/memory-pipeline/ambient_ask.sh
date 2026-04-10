#!/usr/bin/env bash
# Ambient Context Injector for CLI Agents
# Usage: ./ambient_ask.sh <agent> "Your prompt here"
# Example: ./ambient_ask.sh gemini "What is the IP of turing?"

set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <agent_command> <prompt>"
  echo "Example: $0 gemini \"How do I connect to turing?\""
  exit 1
fi

AGENT="$1"
shift
PROMPT="$*"

# Resolve AIKB root relative to this script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIKB_ROOT="$(cd "$DIR/../.." && pwd)"
SEARCH_SCRIPT="$DIR/memory_search.py"

# Quick keyword extraction: drop small words to improve search hit rate
QUERY=$(echo "$PROMPT" | awk '{for(i=1;i<=NF;i++) if(length($i)>3) print $i}')

# Fast, non-semantic lexical search (top 3)
if [ -n "$QUERY" ] && [ -f "$SEARCH_SCRIPT" ]; then
  CONTEXT=$(python3 "$SEARCH_SCRIPT" --query "$QUERY" --limit 3 --no-semantic --json 2>/dev/null | grep -E '"excerpt"|"path"' | sed 's/[",]//g; s/^ *//' || true)
else
  CONTEXT=""
fi

if [ -n "$CONTEXT" ]; then
  # Inject ambient context block
  FULL_PROMPT="<ambient_context>
# The following facts were automatically retrieved from the AIKB based on your prompt:
$CONTEXT
</ambient_context>

$PROMPT"
else
  FULL_PROMPT="$PROMPT"
fi

# Execute the agent
echo "Injecting ambient context and launching $AGENT..."
"$AGENT" "$FULL_PROMPT"
