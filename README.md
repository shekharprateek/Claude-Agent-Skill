# Claude Agent with Dynamic Skills on Amazon Bedrock AgentCore

---

This sample demonstrates how to deploy an AI agent using the **Claude SDK with Amazon Bedrock** on **Amazon Bedrock AgentCore Runtime**, with dynamic skill definitions loaded from Amazon S3.

## What You'll Learn

- Deploy a containerized agent to AgentCore Runtime using Claude SDK
- Load skill definitions dynamically from S3 at runtime
- Configure IAM permissions for agent execution
- Use `--local-build` to avoid Lambda layer injection issues

## Problem
Customers needs Claude Agent SDK's skill system on AgentCore Runtime, but a mismatch between Claude SDK's filesystem-based approach (expecting .claude/skills/ directories with complex nested structures, Python scripts, and interdependent skill.md files) and AgentCore's constraints that limit filesystem access and container size. With an ever-growing skill repository (10-30 skills expanding to 100+) that needs to be shared across multiple agent runtimes, the standard approach of bundling all skills into each container becomes unmanageable and prevents hot updates. Our S3-based solution provides centralized skill storage, dynamic runtime loading, and hot-swappable capabilities essentially solving enterprise-scale skill management challenges that the native Claude Agent SDK can't address on constrained runtime environments.
## Architecture

```
┌──────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  User    │────▶│  AgentCore Runtime  │────▶│   Container     │
│  Request │     │  (Managed Service)  │     │   (HTTP:8080)   │
└──────────┘     └─────────────────────┘     └────────┬────────┘
                                                      │
                         ┌────────────────────────────┼────────────┐
                         │                            ▼            │
                         │  ┌─────────┐       ┌─────────────┐     │
                         │  │   S3    │◀──────│  Claude SDK │     │
                         │  │ Skills  │ load  │  + Bedrock  │     │
                         │  └─────────┘       └─────────────┘     │
                         └─────────────────────────────────────────┘
```

## Prerequisites

* An [AWS account](https://signin.aws.amazon.com/signin) with credentials configured (`aws configure`)
* [Python 3.10](https://www.python.org/downloads/) or later
* [Docker](https://www.docker.com/) installed and running
* Model Access: Claude model enabled in [Amazon Bedrock console](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html)
* AWS Permissions:
  * `BedrockAgentCoreFullAccess` managed policy
  * `AmazonBedrockFullAccess` managed policy

## Quick Start

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd Claude-Agent-Skill
```

### Step 2: Install Dependencies

```bash
pip install bedrock-agentcore anthropic boto3
```

### Step 3: Configure the Agent

```bash
agentcore configure -e claude_sdk_bedrock.py -dt container -dm -ni
```

### Step 4: Deploy to AgentCore Runtime

```bash
# Important: Use --local-build to avoid Lambda layer injection
agentcore launch --local-build
```

### Step 5: Test Your Agent

```bash
# Check status
agentcore status

# Invoke the agent
agentcore invoke '{"prompt": "What skills do you have?"}'

# Try another prompt
agentcore invoke '{"prompt": "Write a Python hello world"}'
```

**Success:** You should see responses that reference the skills loaded from S3.

## S3 Skills Structure

Create an S3 bucket with skill definitions:

```
your-skills-bucket/
└── skills/
    ├── code-analysis/
    │   └── skill.md
    ├── web-research/
    │   └── skill.md
    ├── data-fetcher/
    │   └── skill.md
    ├── document-generator/
    │   └── skill.md
    ├── report-generator/
    │   └── skill.md
    └── data-analysis-workflow/
        └── skill.md
```

Each `skill.md` file contains a description of the skill's capabilities that gets injected into the system prompt.

## IAM Permissions

Add S3 access to your AgentCore execution role:

```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:ListBucket"],
  "Resource": [
    "arn:aws:s3:::your-skills-bucket",
    "arn:aws:s3:::your-skills-bucket/*"
  ]
}
```

## Configuration

| Setting | Value |
|---------|-------|
| Model | `us.anthropic.claude-sonnet-4-20250514-v1:0` |
| Port | 8080 |
| Protocol | HTTP |
| Build | Local (`--local-build`) |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | `us-east-1` |
| `SKILLS_S3_BUCKET` | S3 bucket for skills | `claude-skills-poc-bucket` |
| `ANTHROPIC_MODEL` | Bedrock model ID | `us.anthropic.claude-sonnet-4-20250514-v1:0` |

## Key Implementation Details

### Claude SDK Integration

```python
import anthropic
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Claude SDK with Bedrock backend
claude_client = anthropic.AnthropicBedrock(aws_region=AWS_REGION)

app = BedrockAgentCoreApp()

@app.entrypoint
def handler(event, context):
    response = claude_client.messages.create(
        model=MODEL_ID,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )
    return {"response": response.content[0].text}
```

### Dynamic Skill Loading

Skills are loaded from S3 at container startup and injected into the system prompt:

```python
def load_skills():
    response = s3_client.list_objects_v2(Bucket=SKILLS_S3_BUCKET, Prefix='skills/', Delimiter='/')
    for prefix in response.get('CommonPrefixes', []):
        name = prefix['Prefix'].replace('skills/', '').rstrip('/')
        desc = s3_client.get_object(Bucket=SKILLS_S3_BUCKET, Key=f'skills/{name}/skill.md')
        SKILLS[name] = desc['Body'].read().decode('utf-8')[:200]
```

## Cleanup

```bash
agentcore destroy
```

## Related Resources

* [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
* [Amazon Bedrock AgentCore Samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
* [Claude SDK Documentation](https://docs.anthropic.com/en/api/claude-on-amazon-bedrock)
* [AgentCore Starter Toolkit](https://github.com/aws/bedrock-agentcore-starter-toolkit)
