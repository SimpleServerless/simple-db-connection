from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
import logging
from utils import Router
import utils
import db_utils
import student_sql
from aws_lambda_powertools.utilities.typing import LambdaContext

log: Logger = Logger()
Logger("botocore").setLevel(logging.INFO)
Logger("urllib3").setLevel(logging.INFO)

app = APIGatewayHttpResolver()
router: Router = Router()
transaction = db_utils.transaction

# Handler
@log.inject_lambda_context()
def handler(event: dict, context: LambdaContext) -> dict:
    print(event)
    return app.resolve(event, context)


#
# Query Actions
#

@app.get("/students")
@transaction
def list_students(conn) -> dict:
    with conn.cursor() as curs:
        curs.execute(student_sql.GET_STUDENTS, )
        item_list = curs.fetchall()
    item_list = utils.camelfy(item_list)
    return item_list


@app.get("/students/<student_id>") # Resolves for a ReST endpoint
@transaction
def get_student(conn, student_id) -> dict:
    with conn.cursor() as curs:
        curs.execute(student_sql.GET_STUDENT_BY_STUDENT_ID, {'student_id': student_id})
        item = curs.fetchone()
    item = utils.camelfy(item)

    return item


#
# Mutation Actions
#

@app.post("/students")
@transaction
def create_student(conn) -> dict:
    student_uuid = utils.generate_uuid()
    student_in = app.current_event.json_body
    student_in['studentUuid'] = student_uuid
    return save_student(conn, student_in)


@app.put("/students/<student_id>") # Resolves for a ReST endpoint
@transaction
def update_student(conn, student_id) -> dict:
    student_in = app.current_event.json_body
    existing_student = get_student(student_id)
    # Merge existing values with incoming values with incoming values taking precedence
    if existing_student:
        student_in = {**existing_student, **student_in}
    else:
        raise Exception(f"Student with studentId {student_in.get('studentId')} not found for update")
    return save_student(conn, student_in)


def save_student(conn, student_in) -> dict:
    with conn.cursor() as curs:
        curs.execute(student_sql.SAVE_STUDENT, {
            'student_uuid': student_in['studentUuid'],
            'student_id': student_in['studentId'],
            'first_name': student_in['firstName'],
            'last_name': student_in['lastName'],
            'status': student_in['status'],
            'program_id': student_in['programId'],
            'active': True,
            'updated_by': 'system',
            'created_by': 'system'
        })
        item = curs.fetchone()
    item = utils.camelfy(item)

    return item


@app.delete("/students/<student_id>")
@transaction
def delete_student(conn, student_id) -> dict:
    with conn.cursor() as curs:
        curs.execute(student_sql.DELETE_STUDENT, {'student_id': student_id})
    return {'result': 'success'}