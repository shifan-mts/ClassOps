import os
import boto3
from decimal import Decimal
import json
import datetime

def decimal_to_native(obj):
    """Recursively converts DynamoDB Decimals to native Python ints/floats for JSON serialization."""
    if isinstance(obj, list):
        return [decimal_to_native(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    return obj

def sanitize_for_dynamodb(obj):
    """Recursively converts unsupported types (like datetime) to strings for DynamoDB."""
    if isinstance(obj, list):
        return [sanitize_for_dynamodb(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: sanitize_for_dynamodb(v) for k, v in obj.items()}
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    return obj
