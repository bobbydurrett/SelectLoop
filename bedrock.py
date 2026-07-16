import boto3
import json
import sys
from botocore.config import Config
from botocore.exceptions import ReadTimeoutError

def getresponse(prompt_text, timeout_secs):
    """
    
    Takes an input string as a prompt and passes it to Bedrock
    returning the resulting string.
    
    Timeout_secs is how long an inference is allowed to run.
    
    """
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 6000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    }
                ]
            }
        ]
    })
    
    config = Config(
        connect_timeout=10,            # seconds to establish connection
        read_timeout=timeout_secs,     # seconds waiting for Bedrock response
        retries={
            "max_attempts": 2
        }
    )

    bedrock = boto3.client(
        service_name='bedrock-runtime',config=config)
    
    try:
        response = bedrock.invoke_model(
            modelId="us.anthropic.claude-sonnet-4-6",
            body=body,
            contentType="application/json",
            accept="application/json"
        )
    except ReadTimeoutError:
        return "ERROR: Bedrock timed out"
    except Exception as e:
        return f"ERROR: {e}"
        
    temp = response['body'].read().decode()
    
    # Parse the JSON string
    data = json.loads(temp)
    
    # Extract the text content
    text_content = data["content"][0]["text"]

    return text_content
