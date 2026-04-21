import os
import boto3
from decimal import Decimal
import json
from botocore.exceptions import ClientError

# Setup boto3 resource
# Using os.getenv for credentials and region (User should add them to .env/Render)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'eu-north-1')
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE')

if not DYNAMODB_TABLE_NAME:
    raise ValueError("CRITICAL ERROR: DYNAMODB_TABLE environment variable is not set. Please set it in your Render environment.")

dynamodb = boto3.resource(
    'dynamodb',
    region_name='eu-north-1',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Verify table exists on initialization
try:
    table.load()
    print(f"Successfully connected to DynamoDB table: {DYNAMODB_TABLE_NAME} in region eu-north-1")
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
        print(f"CRITICAL ERROR: DynamoDB table '{DYNAMODB_TABLE_NAME}' not found in region 'eu-north-1'.")
        print("Please check your AWS Console to ensure the table exists and names match exactly (case-sensitive).")
    else:
        print(f"Error connecting to DynamoDB: {e}")

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

# --- Core Helper Functions for Auth & Sync ---

def get_teacher(email):
    try:
        response = table.get_item(
            Key={
                'PK': f"TEACHER#{email}",
                'SK': 'METADATA'
            }
        )
        return decimal_to_native(response.get('Item'))
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"CRITICAL ERROR in get_teacher: DynamoDB table '{DYNAMODB_TABLE_NAME}' not found.")
            print("Please verify the AWS_REGION and DYNAMODB_TABLE_NAME environment variables.")
        raise

def put_teacher(teacher_data):
    teacher_data['PK'] = f"TEACHER#{teacher_data['email']}"
    teacher_data['SK'] = 'METADATA'
    table.put_item(Item=teacher_data)
    return teacher_data

def get_course(email, course_id):
    response = table.get_item(
        Key={
            'PK': f"TEACHER#{email}",
            'SK': f"COURSE#{course_id}"
        }
    )
    return decimal_to_native(response.get('Item'))

def put_course(email, course_data):
    course_id = course_data.get('id')
    course_data['PK'] = f"TEACHER#{email}"
    course_data['SK'] = f"COURSE#{course_id}"
    table.put_item(Item=course_data)
    return course_data

def sync_student(course_id, student_data):
    roll = student_data.get('roll_number')
    student_data['PK'] = f"COURSE#{course_id}"
    student_data['SK'] = f"STUDENT#{roll}"
    table.put_item(Item=student_data)
    return student_data

def get_courses_by_teacher(email):
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": f"TEACHER#{email}",
            ":sk_prefix": "COURSE#"
        }
    )
    return decimal_to_native(response.get('Items', []))

def get_students_by_course(course_id):
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": f"COURSE#{course_id}",
            ":sk_prefix": "STUDENT#"
        }
    )
    return decimal_to_native(response.get('Items', []))

def get_assignments_by_course(course_id):
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": f"COURSE#{course_id}",
            ":sk_prefix": "ASSIGNMENT#"
        }
    )
    return decimal_to_native(response.get('Items', []))

def put_assignment(course_id, assignment_data):
    assignment_id = assignment_data.get('id') or assignment_data.get('google_assignment_id')
    assignment_data['PK'] = f"COURSE#{course_id}"
    assignment_data['SK'] = f"ASSIGNMENT#{assignment_id}"
    table.put_item(Item=assignment_data)
    return assignment_data

def get_assignment(course_id, assignment_id):
    response = table.get_item(
        Key={
            'PK': f"COURSE#{course_id}",
            'SK': f"ASSIGNMENT#{assignment_id}"
        }
    )
    return decimal_to_native(response.get('Item'))
def get_attendance_records(course_id, date=None):
    if date:
        response = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": f"COURSE#{course_id}",
                ":sk_prefix": f"ATTENDANCE#{date}#"
            }
        )
    else:
        response = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": f"COURSE#{course_id}",
                ":sk_prefix": "ATTENDANCE#"
            }
        )
    return decimal_to_native(response.get('Items', []))

def put_attendance_record(course_id, record_data):
    date = record_data.get('date')
    roll = record_data.get('student_id') # mapping student_id to roll_number
    record_data['PK'] = f"COURSE#{course_id}"
    record_data['SK'] = f"ATTENDANCE#{date}#{roll}"
    table.put_item(Item=record_data)
    return record_data

def get_material_targets_by_course(course_id):
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": f"COURSE#{course_id}",
            ":sk_prefix": "TARGET#"
        }
    )
    return decimal_to_native(response.get('Items', []))

def put_material_target(course_id, target_data):
    target_id = target_data.get('id')
    target_data['PK'] = f"COURSE#{course_id}"
    target_data['SK'] = f"TARGET#{target_id}"
    table.put_item(Item=target_data)
    return target_data

def get_timetable_slots_by_course(course_id):
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": f"COURSE#{course_id}",
            ":sk_prefix": "SLOT#"
        }
    )
    return decimal_to_native(response.get('Items', []))

def put_timetable_slot(course_id, slot_data):
    slot_id = slot_data.get('id')
    slot_data['PK'] = f"COURSE#{course_id}"
    slot_data['SK'] = f"SLOT#{slot_id}"
    table.put_item(Item=slot_data)
    return slot_data

def delete_timetable_slot(course_id, slot_id):
    table.delete_item(
        Key={
            'PK': f"COURSE#{course_id}",
            'SK': f"SLOT#{slot_id}"
        }
    )

def get_courses_by_google_ids(google_course_ids):
    # Since we don't have a GSI, we'll scan the table. 
    # For a small to medium app, this is acceptable.
    response = table.scan(
        FilterExpression="begins_with(PK, :pk_prefix) AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk_prefix": "TEACHER#",
            ":sk_prefix": "COURSE#"
        }
    )
    all_courses = decimal_to_native(response.get('Items', []))
    matched_courses = [c for c in all_courses if c.get('google_course_id') in google_course_ids]
    return matched_courses
