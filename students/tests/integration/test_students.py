import json
import sys
import os
import pytest
from pathlib import Path

from aws_lambda_powertools.utilities.typing import LambdaContext

# Get the service module's base directory
service_dir = Path(__file__).parent.parent.parent
# Add the source directory to the Python path
src_dir = service_dir / "src"
sys.path.insert(0, str(src_dir))

# Add the service root directory to import run_local.py contents if needed
sys.path.insert(0, str(service_dir))

import lambda_function
from AppShared import utils

class MockContext(LambdaContext):
    def __init__(self,
                 invoked_function_arn="arn:aws:lambda:us-west-2:0000000000:function:mock_function-name:dev",
                 function_name="mock_function_name",
                 memory_limit_in_mb=64,
                 aws_request_id="mock_id"):
        print("Mock context initialized")

mock_context = MockContext

def test_list_students_integration():
    """
    Integration test that replicates what happens when run_local.py is ran with LIST_STUDENTS_REST.
    It connects to the actual database and validates that it gets a list of students greater than 1 record.
    """

    list_students_event = utils.create_rest_event("GET", "/students")

    # Call the lambda handler with the event and context
    result = lambda_function.handler(list_students_event, mock_context)

    # Verify that the response is successful
    assert result["statusCode"] == 200

    # Parse the response body
    body = json.loads(result["body"])

    # Verify that we got a list of students
    assert isinstance(body, list)

    # Verify that there are more than 1 student records
    assert len(body) > 1, f"Expected more than 1 student record, but got {len(body)}"

    # Verify that each student has the required fields
    for student in body:
        assert "studentId" in student
        assert "firstName" in student
        assert "lastName" in student
        assert "status" in student
        assert "programId" in student


def test_get_student_by_student_id():
    """
    Integration test that replicates what happens when run_local.py is ran with GET_STUDENT_BY_STUDENT_ID.
    It connects to the actual database and validates that it gets a student record for student_id=1.
    """

    get_student_event = utils.create_rest_event("GET", "/students/1")

    # Call the lambda handler with the event and context
    result = lambda_function.handler(get_student_event, mock_context)

    # Verify that the response is successful
    assert result["statusCode"] == 200

    # Parse the response body
    body = json.loads(result["body"])

    # Verify that we got a student record
    assert isinstance(body, dict)

    # Verify that the student has the required fields
    assert "studentId" in body
    assert body["studentId"] == 1
    assert "firstName" in body
    assert "lastName" in body
    assert "status" in body
    assert "programId" in body