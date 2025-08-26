import json
import sys
import os
from aws_lambda_powertools.utilities.typing import LambdaContext

import utils

events = {
    "LIST_PROGRAMS": utils.create_rest_event("GET", "/programs"),

    "GET_PROGRAM_BY_PROGRAM_ID": utils.create_rest_event("GET", "/programs/c69ce217-c08d-4e50-bdda-4dfe4f9a9a3c"),
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
