import json
import sys
import os
import pytest
from pathlib import Path

from aws_lambda_powertools.utilities.typing import LambdaContext

import utils

# Add the source directory to the Python path so we can import the lambda function
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
import lambda_function

# Import the event from run_local.py
sys.path.append(str(Path(__file__).parent.parent.parent))

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
