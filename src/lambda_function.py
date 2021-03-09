from aws_lambda_powertools import Logger
import logging
from utils import Invocation
from utils import Router
import utils
import db_utils
import sql
import uuid
from aws_lambda_powertools.utilities.typing import LambdaContext

log: Logger = Logger()
Logger("botocore").setLevel(logging.INFO)
Logger("urllib3").setLevel(logging.INFO)

router: Router = Router()
transaction = db_utils.transaction

# Handler
@log.inject_lambda_context()
def handler(event: dict, context: LambdaContext) -> dict:
    return Invocation(router, event).call()


#
# Query Actions
#

@router.rest("GET", "/students") # Resolves for a ReST endpoint
@router.direct("list_students")
@transaction
def list_students(conn, args: dict) -> dict:
    with conn.cursor() as curs:
        curs.execute(sql.GET_STUDENTS, )
        item_list = curs.fetchall()
    item_list = utils.camelfy(item_list)
    return item_list


@router.rest("GET", "/students/{studentId}") # Resolves for a ReST endpoint
@transaction
def get_student(conn, args: dict) -> dict:
    student_id = args.get('studentId')
    with conn.cursor() as curs:
        curs.execute(sql.GET_STUDENT_BY_STUDENT_ID, (student_id,))
        item = curs.fetchone()
    item = utils.camelfy(item)

    return item


#
# Mutation Actions
#
@router.rest("PUT", "/students") # Resolves for a ReST endpoint
@transaction
def save_student(conn, args: dict) -> dict:
    student = args['student']
    if 'studentUuid' not in student:
        student['studentUuid'] = uuid.uuid4()

    with conn.cursor() as curs:
        curs.execute(sql.SAVE_STUDENT, (
                                        student['studentUuid'],
                                        student['firstName'],
                                        student['lastName'],
                                        student['status'],
                                        student['programId'],
                                        True,
                                        'system',
                                        'system'))



    return student
