#!/bin/bash
# Create standard labels for PR workflow

LABELS="agent-created:0366d6:Created by AI agent
needs-review:fbca04:Awaiting code review
needs-fixes:d93f0b:Review found issues
approved:0e8a16:Ready to merge
blocked:b60205:Cannot proceed"

echo "$LABELS" | while IFS=: read -r name color desc; do
  gh label create "$name" --color "$color" --description "$desc" 2>/dev/null || echo "Label '$name' exists"
done
echo "✅ Labels setup complete"
