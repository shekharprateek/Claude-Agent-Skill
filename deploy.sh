#!/bin/bash
# Deploy Claude Agent to AgentCore Runtime

set -e

echo "=== Claude Agent Deployment ==="

# Configure agent
echo "Configuring agent..."
agentcore configure -e claude_sdk_bedrock.py -dt container -dm -ni

# Deploy with local build (required to avoid Lambda layer injection)
echo "Building and deploying..."
agentcore launch --local-build

echo ""
echo "=== Deployment Complete ==="
echo "Test with: agentcore invoke '{\"prompt\": \"What skills do you have?\"}'"
