#!/usr/bin/env python3
"""Claude Agent with Skills - Using Claude SDK with Bedrock on AgentCore Runtime"""

import os
import boto3
import anthropic
from bedrock_agentcore.runtime import BedrockAgentCoreApp

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
SKILLS_S3_BUCKET = os.getenv('SKILLS_S3_BUCKET', 'claude-skills-poc-bucket')
MODEL_ID = os.getenv('ANTHROPIC_MODEL', 'us.anthropic.claude-sonnet-4-20250514-v1:0')

s3_client = boto3.client('s3', region_name=AWS_REGION)

# Claude SDK with Bedrock backend
claude_client = anthropic.AnthropicBedrock(aws_region=AWS_REGION)

SKILLS = {}

def load_skills():
    """Load skill definitions from S3 at startup."""
    global SKILLS
    try:
        response = s3_client.list_objects_v2(Bucket=SKILLS_S3_BUCKET, Prefix='skills/', Delimiter='/')
        for prefix in response.get('CommonPrefixes', []):
            name = prefix['Prefix'].replace('skills/', '').rstrip('/')
            if name:
                try:
                    desc = s3_client.get_object(Bucket=SKILLS_S3_BUCKET, Key=f'skills/{name}/skill.md')['Body'].read().decode('utf-8')
                    SKILLS[name] = desc[:200]
                except:
                    SKILLS[name] = f"Skill: {name}"
        print(f"Loaded {len(SKILLS)} skills from S3")
    except Exception as e:
        print(f"Skills loading skipped: {e}")

load_skills()

app = BedrockAgentCoreApp()

@app.entrypoint
def handler(event, context):
    """AgentCore entrypoint handler using Claude SDK."""
    prompt = event.get('prompt', 'Hello') if event else 'Hello'
    
    skills_info = "\n".join([f"- {name}: {desc}" for name, desc in SKILLS.items()]) if SKILLS else "No skills loaded"
    system_prompt = f"You are a helpful AI assistant. Available skills:\n{skills_info}\nDescribe your capabilities when asked."

    response = claude_client.messages.create(
        model=MODEL_ID,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return {
        "response": response.content[0].text,
        "skills_loaded": len(SKILLS),
        "skills_available": list(SKILLS.keys())
    }

if __name__ == "__main__":
    app.run()
