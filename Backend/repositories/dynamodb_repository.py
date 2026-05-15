import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from utils.data_sanitizer import decimal_to_native, sanitize_for_dynamodb

# Load environment variables from .env if present
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BACKEND_DIR, ".env"), encoding="utf-8-sig")


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# Setup boto3 resource
# Using os.getenv for credentials and region
IS_LOCAL = _env_bool('IS_LOCAL')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'eu-north-1')
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE') or os.getenv('DYNAMODB_TABLE_NAME')

if not DYNAMODB_TABLE_NAME:
    if IS_LOCAL:
        DYNAMODB_TABLE_NAME = "ClassOps_Data"
    else:
        raise ValueError("CRITICAL ERROR: DYNAMODB_TABLE environment variable is not set. Please set it in your environment.")

# Initialize DynamoDB Resource
if IS_LOCAL:
    # Local DynamoDB configuration (Docker)
    # If running outside docker, localhost:8000 works.
    # If running inside docker, use the service name 'dynamodb-local:8000'.
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL', 'http://localhost:8000')
    print(f"Connecting to local DynamoDB at {endpoint_url}")
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        endpoint_url=endpoint_url,
        aws_access_key_id='local',
        aws_secret_access_key='local'
    )
else:
    print(f"Connecting to production DynamoDB in {AWS_REGION}")
    aws_resource_kwargs = {
        'region_name': AWS_REGION,
    }
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        aws_resource_kwargs.update(
            {
                'aws_access_key_id': AWS_ACCESS_KEY_ID,
                'aws_secret_access_key': AWS_SECRET_ACCESS_KEY,
            }
        )
    if AWS_SESSION_TOKEN:
        aws_resource_kwargs['aws_session_token'] = AWS_SESSION_TOKEN
    dynamodb = boto3.resource(
        'dynamodb',
        **aws_resource_kwargs
    )

table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def ensure_table_exists():
    """Verifies table existence; creates it if running locally and missing."""
    try:
        table.load()
        print(f"Successfully connected to table: {DYNAMODB_TABLE_NAME}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            if IS_LOCAL:
                print(f"Table '{DYNAMODB_TABLE_NAME}' not found. Creating it locally...")
                dynamodb.create_table(
                    TableName=DYNAMODB_TABLE_NAME,
                    KeySchema=[
                        {'AttributeName': 'PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'PK', 'AttributeType': 'S'},
                        {'AttributeName': 'SK', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                )
                table.wait_until_exists()
                print(f"Table '{DYNAMODB_TABLE_NAME}' created successfully.")
            else:
                print(f"CRITICAL ERROR: DynamoDB table '{DYNAMODB_TABLE_NAME}' not found in region '{AWS_REGION}'.")
                raise
        else:
            print(f"Error connecting to DynamoDB: {e}")
            raise

# Run the existence check/creation
ensure_table_exists()

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
    table.put_item(Item=sanitize_for_dynamodb(teacher_data))
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
    table.put_item(Item=sanitize_for_dynamodb(course_data))
    return course_data

def sync_student(course_id, student_data):
    roll = student_data.get('roll_number')
    student_data['PK'] = f"COURSE#{course_id}"
    student_data['SK'] = f"STUDENT#{roll}"
    table.put_item(Item=sanitize_for_dynamodb(student_data))
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

def get_all_courses():
    response = table.scan(
        FilterExpression="begins_with(PK, :pk_prefix) AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk_prefix": "TEACHER#",
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
    table.put_item(Item=sanitize_for_dynamodb(assignment_data))
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
    table.put_item(Item=sanitize_for_dynamodb(record_data))
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
    table.put_item(Item=sanitize_for_dynamodb(target_data))
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
    table.put_item(Item=sanitize_for_dynamodb(slot_data))
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

def get_feedback(course_id, assignment_id, student_id):
    response = table.get_item(
        Key={
            'PK': f"COURSE#{course_id}",
            'SK': f"FEEDBACK#{assignment_id}#{student_id}"
        }
    )
    return decimal_to_native(response.get('Item'))

def put_feedback(course_id, assignment_id, student_id, feedback_data):
    feedback_data['PK'] = f"COURSE#{course_id}"
    feedback_data['SK'] = f"FEEDBACK#{assignment_id}#{student_id}"
    table.put_item(Item=sanitize_for_dynamodb(feedback_data))
    return feedback_data

def put_evaluation(course_id, student_id, eval_data):
    eval_data['PK'] = f"COURSE#{course_id}"
    eval_data['SK'] = f"EVALUATION#{student_id}"
    table.put_item(Item=sanitize_for_dynamodb(eval_data))
    return eval_data

def get_evaluations_by_course(course_id):
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": f"COURSE#{course_id}",
            ":sk_prefix": "EVALUATION#"
        }
    )
    return decimal_to_native(response.get('Items', []))

# --- RBAC Operations ---

def get_role(role_name):
    response = table.get_item(
        Key={
            'PK': f"ROLE#{role_name}",
            'SK': 'METADATA'
        }
    )
    return decimal_to_native(response.get('Item'))

def put_role(role_data):
    role_name = role_data.get('name')
    role_data['PK'] = f"ROLE#{role_name}"
    role_data['SK'] = 'METADATA'
    table.put_item(Item=sanitize_for_dynamodb(role_data))
    return role_data

def delete_role(role_name):
    table.delete_item(
        Key={
            'PK': f"ROLE#{role_name}",
            'SK': 'METADATA'
        }
    )

def scan_all_roles():
    response = table.scan(
        FilterExpression="begins_with(PK, :pk_prefix) AND SK = :sk",
        ExpressionAttributeValues={
            ":pk_prefix": "ROLE#",
            ":sk": "METADATA"
        }
    )
    return decimal_to_native(response.get('Items', []))

def get_user_role(email):
    response = table.get_item(
        Key={
            'PK': f"USER_ROLE#{email}",
            'SK': 'METADATA'
        }
    )
    return decimal_to_native(response.get('Item'))

def put_user_role(email, role_name):
    data = {
        'PK': f"USER_ROLE#{email}",
        'SK': 'METADATA',
        'email': email,
        'role': role_name
    }
    table.put_item(Item=sanitize_for_dynamodb(data))
    return data

def delete_user_role(email):
    table.delete_item(
        Key={
            'PK': f"USER_ROLE#{email}",
            'SK': 'METADATA'
        }
    )

def scan_all_user_roles():
    response = table.scan(
        FilterExpression="begins_with(PK, :pk_prefix) AND SK = :sk",
        ExpressionAttributeValues={
            ":pk_prefix": "USER_ROLE#",
            ":sk": "METADATA"
        }
    )
    return decimal_to_native(response.get('Items', []))
