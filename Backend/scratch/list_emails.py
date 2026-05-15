import os
import sys
from dotenv import load_dotenv

# Add Backend to path
BACKEND_DIR = os.getcwd()
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BACKEND_DIR, ".env"), encoding="utf-8-sig")

from repositories import dynamodb_repository as db

def list_all_emails():
    print("Scanning all records in DynamoDB for emails...")
    emails = set()
    try:
        # Scan the entire table
        response = db.table.scan()
        items = response.get('Items', [])
        
        while 'LastEvaluatedKey' in response:
            response = db.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
            
        for item in items:
            pk = item.get('PK', '')
            
            # Check PK for TEACHER#email or USER_ROLE#email
            if pk.startswith('TEACHER#'):
                emails.add(pk.replace('TEACHER#', ''))
            elif pk.startswith('USER_ROLE#'):
                emails.add(pk.replace('USER_ROLE#', ''))
            
            # Check email attribute
            if 'email' in item:
                emails.add(item['email'])
                
        if not emails:
            print("No emails found in the entire table.")
        else:
            print(f"Found {len(emails)} unique emails in the system:")
            for email in sorted(list(emails)):
                print(f"- {email}")
    except Exception as e:
        print(f"Error scanning table: {e}")

if __name__ == "__main__":
    list_all_emails()
