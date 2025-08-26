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
        curs.execute(student_sql.GET_STUDENT_BY_STUDENT_ID, (student_id,))
        item = curs.fetchone()
    item = utils.camelfy(item)

    return item




#
# Mutation Actions
#
@app.post("/students/<student_id>") # Resolves for a ReST endpoint
@transaction
def save_student(conn, student_id) -> dict:
    with conn.cursor() as curs:
        student_in = app.current_event.json_body
        student_existing = get_student(student_id)
        # Merge student_in and student_existing, giving preference to student_in
        if student_existing is not None:
            student_in = {**student_existing, **student_in}
        curs.execute(student_sql.SAVE_STUDENT, (
                                        student_in['studentUuid'],
                                        student_in['studentId'],
                                        student_in['firstName'],
                                        student_in['lastName'],
                                        student_in['status'],
                                        student_in['programId'],
                                        True,
                                        'system',
                                        'system'))
        item = curs.fetchone()
    item = utils.camelfy(item)

    return item
