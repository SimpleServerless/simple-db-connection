import json
import sys
import os
from aws_lambda_powertools.utilities.typing import LambdaContext

events = {

    "LIST_STUDENTS_DIRECT":
        """
        {
            "route": "list_students"
        }
        """,

    "LIST_STUDENTS_REST":
        """
        {
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
            "isBase64Encoded": false
        }
        """,

    "GET_STUDENT_BY_STUDENT_ID_REST":
        """
        {
            "version": "2.0",
            "routeKey": "GET /students/{studentId}",
            "rawPath": "/students/1234",
            "rawQueryString": "testParam=4567&otherParam=8888",
            "headers": {
              "accept": "application/json"
            },
            "queryStringParameters": {
              "otherParam": "8888",
              "testParam": "4567"
            },
            "pathParameters": {
              "studentId": "1"
            },
            "requestContext": {
                "accountId": "778590694111",
                "apiId": "rnkhtugxlh",
                "domainName": "rnkhtugxlh.execute-api.us-east-2.amazonaws.com",
                "domainPrefix": "rnkhtugxlh",
                "http": {
                  "method": "GET",
                  "path": "/students",
                  "protocol": "HTTP/1.1",
                  "sourceIp": "216.147.121.237",
                  "userAgent": "PostmanRuntime/7.45.0"
            },
            "isBase64Encoded": false
        }
        """,

    "SAVE_STUDENT_REST":
        """
        {
            "version": "2.0",
            "routeKey": "POST /students",
            "rawPath": "/students",
            "rawQueryString": "testParam=4567&otherParam=8888",
            "headers": {
              "accept": "application/json"
            },
            "queryStringParameters": {
              "otherParam": "8888",
              "testParam": "4567"
            },
            "pathParameters": {
            },
            "body": "{\\\"student\\\": {\\\"studentUuid\\\": \\\"7812233d-9289-4442-8cbb-92535124e9a7\\\", \\\"firstName\\\": \\\"Jack\\\", \\\"lastName\\\": \\\"Harkness\\\", \\\"status\\\": \\\"ENROLLED\\\", \\\"programId\\\": \\\"d958c587-db7b-41f9-9954-c33dc56e08f5\\\"}}",
            "isBase64Encoded": false
        }
        """

}


class MockContext(LambdaContext):
    def __init__(self,
                 invoked_function_arn="arn:aws:lambda:us-west-2:0000000000:function:mock_function-name:dev",
                 function_name="mock_function_name",
                 memory_limit_in_mb=64,
                 aws_request_id="mock_id"):
        print("Mock context initialized")


def run(event_string, handler_function):
    # Initialize a context to pass into the halder method
    context = MockContext

    # Create an event dictionary from event_string
    print("\nEVENT:")
    print(event_string)
    event = json.loads(event_string)

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
    from students.src import lambda_function

    event_name = sys.argv[1]
    print("Running event: " + event_name)
    run(events[event_name], lambda_function.handler)
