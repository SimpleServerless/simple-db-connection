import json
import sys
import os
from aws_lambda_powertools.utilities.typing import LambdaContext
from AppShared import utils

events = {
    "LIST_STUDENTS": {
        "version": "2.0",
        "routeKey": "GET /students",
        "rawPath": "/students",
        "headers": {
          "accept": "application/json"
        },
        "requestContext": {
            "http": {
              "method": "GET",
              "path": "/students"
            },
            "stage": "$default"
        },
        "isBase64Encoded": False
    },

    "LIST_STUDENTS_EASY": utils.create_rest_event("GET", "/students"),

    "GET_STUDENT_BY_STUDENT_ID": utils.create_rest_event("GET", "/students/1"),

    "GET_STUDENT_BY_STUDENT_NAME": utils.create_rest_event("GET", "/students/name/Jones"),

    "CREATE_STUDENT": utils.create_rest_event("POST", "/students", {"firstName": "Jane", "last_name": "Doe", "status": "ENROLLED"}),

    "UPDATE_STUDENT": utils.create_rest_event("PUT", "/students/1", {"status": "ENROLLED"}),

}


class MockContext(LambdaContext):
    def __init__(self,
                 invoked_function_arn="arn:aws:lambda:us-west-2:0000000000:function:mock_function-name:dev",
                 function_name="mock_function_name",
                 memory_limit_in_mb=64,
                 aws_request_id="mock_id"):
        print("Mock context initialized")


def run(event_key, handler_function):
    # Initialize a context to pass into the handler method
    context = MockContext

    # Get the event dictionary from events
    event = events[event_key]

    # For backwards compatibility, handle string events
    if isinstance(event, str):
        event = json.loads(event)

    # Print event in a readable format
    print("\nEVENT:")
    print(json.dumps(event, indent=4))

    result = handler_function(event, context)

    # Log the result of the main handler as json
    print("\nRESULT:")
    print("\n" + json.dumps(result, indent=4, sort_keys=True, default=str))
    print("\n\nBODY:")
    body = json.loads(result["body"])
    print("\n" + json.dumps(body, indent=4, sort_keys=True, default=str))
    return result


if __name__ == '__main__':
    sys.path.append(os.getcwd())
    from src import lambda_function

    event_name = sys.argv[1]
    print("Running event: " + event_name)
    run(event_name, lambda_function.handler)
