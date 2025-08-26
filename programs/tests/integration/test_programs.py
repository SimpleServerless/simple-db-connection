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

# Now import the lambda_function from the current service's src directory
import lambda_function
import utils

class MockContext(LambdaContext):
    def __init__(self,
                 invoked_function_arn="arn:aws:lambda:us-west-2:0000000000:function:mock_function-name:dev",
                 function_name="mock_function_name",
                 memory_limit_in_mb=64,
                 aws_request_id="mock_id"):
        print("Mock context initialized")

mock_context = MockContext

def test_list_programs():
    list_programs_event = utils.create_rest_event("GET", "/programs")

    # Call the lambda handler with the event and context
    result = lambda_function.handler(list_programs_event, mock_context)

    # Verify that the response is successful
    assert result["statusCode"] == 200

    # Parse the response body
    body = json.loads(result["body"])

    # Verify that we got a list of programs
    assert isinstance(body, list)

    # Verify that there are more than 1 program records
    assert len(body) > 1, f"Expected more than 1 program record, but got {len(body)}"

    # Verify that each program has the required fields
    program = body[0]
    assert "programId" in program
    assert "name" in program
    assert "code" in program


def test_get_program_by_id():
    program_id = "c69ce217-c08d-4e50-bdda-4dfe4f9a9a3c"
    get_program_event = utils.create_rest_event("GET", f"/programs/{program_id}")

    # Call the lambda handler with the event and context
    result = lambda_function.handler(get_program_event, mock_context)

    # Verify that the response is successful
    assert result["statusCode"] == 200

    # Parse the response body
    body = json.loads(result["body"])

    # Verify that we got a single program record
    assert isinstance(body, dict)

    # Verify that the program has the required fields
    assert body["programId"] == program_id
    assert "name" in body
    assert "code" in body
