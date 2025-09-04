import sys
import os
import json
import pytest

# Add the src directory to the path so we can import the lambda function
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
# Add the shared directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../shared/src')))

# Import the lambda function
import lambda_function
from AppShared import utils

class MockContext:
    def __init__(self,
                 invoked_function_arn="arn:aws:lambda:us-west-2:0000000000:function:mock_function-name:dev",
                 function_name="mock_function_name",
                 memory_limit_in_mb=64,
                 aws_request_id="mock_id"):
        pass

@pytest.fixture
def list_classes_event():
    return utils.create_rest_event("GET", "/classes")

def test_list_classes(list_classes_event):
    """Test that we can list classes from the database"""
    # Call the handler function with the event
    response = lambda_function.handler(list_classes_event, MockContext())

    # Parse the response body
    body = json.loads(response["body"])

    # Assert we got a valid response
    assert response["statusCode"] == 200

    # Check that we got at least one class in the list
    # Note: This test assumes there's at least one class in the database
    assert isinstance(body, list)
    assert len(body) > 0

    # Verify the structure of the first class
    first_class = body[0]
    assert "classId" in first_class
    assert "className" in first_class
    assert "hoursPerWeek" in first_class
    assert "programId" in first_class
    assert "active" in first_class


