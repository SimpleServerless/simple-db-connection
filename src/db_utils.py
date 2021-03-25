from contextlib import contextmanager
from functools import wraps
import boto3
from botocore.exceptions import ClientError
import base64
import json
import psycopg2
from psycopg2 import _connect
from psycopg2.extras import RealDictCursor
from aws_lambda_powertools import Logger
import logging

log = Logger()
Logger("botocore").setLevel(logging.INFO)
Logger("urllib3").setLevel(logging.INFO)

secret_client = boto3.client('secretsmanager')
ssm = boto3.client('ssm')

connection: _connect = None
db_user = None
db_password = None

@contextmanager
def transaction_wrapper(name="transaction_wrapper", **kwargs):
    global connection, db_user, db_password

    # Lazy load credentials. Should only happen on cold start
    if db_user is None:
        # Get credentials form parameter store
        db_user, db_password = get_db_credentials_from_sm()
        # Get credentials from secret manager
        # db_user, db_password = get_db_credentials_from_sm()
    log.debug("User: " + db_user)

    try:
        if connection is None or connection.closed > 0:
            connection = psycopg2.connect(user=db_user,
                                          password=db_password,
                                          sslmode='prefer',
                                          connect_timeout=5,
                                          cursor_factory=RealDictCursor)

            log.info("New DB connection created")

        yield connection
        connection.commit()
    except Exception as e:
        if connection is not None:
            connection.rollback()
        raise e
    finally:
        if connection is not None:
            connection.reset()


# Creates a connection per-transaction, committing when complete or rolling back if there is an exception.
# It also ensures that the conn is reset when done.
def transaction(func):
    @wraps(func)
    def inner(*args, **kwargs):
        with transaction_wrapper(name=func.__name__) as conn:
            return func(conn, *args, **kwargs)
    return inner


# Here's how you can get credentials stored like {"username": "myuser", "password": "mypassword"} from secrets manager
def get_db_credentials_from_sm() -> tuple:
    log.info('Retrieving db credentials from SecretsManager')
    secret_key = "simple-serverless/db-credentials"
    try:
        get_secret_value_response = secret_client.get_secret_value(SecretId=secret_key)
        log.debug("retrieved credentials")

        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            cred_dict = json.loads(secret)
            return cred_dict['username'], cred_dict['password']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return decoded_binary_secret,

    except ClientError as e:
        print(e)
        exit("Request failed ClientError retrieving {} : {}".format(secret_key, e))
    except Exception as e:
        print(e)
        exit("Request failed Exception retrieving {} : {}".format(secret_key, e))