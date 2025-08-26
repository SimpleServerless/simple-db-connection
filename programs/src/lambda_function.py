from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
import logging
import utils
import db_utils
import program_sql
from aws_lambda_powertools.utilities.typing import LambdaContext

log: Logger = Logger()
Logger("botocore").setLevel(logging.INFO)
Logger("urllib3").setLevel(logging.INFO)

app = APIGatewayHttpResolver()
transaction = db_utils.transaction

# Handler
@log.inject_lambda_context()
def handler(event: dict, context: LambdaContext) -> dict:
    print(event)
    return app.resolve(event, context)


#
# Query Actions
#

@app.get("/programs")
@transaction
def list_programs(conn) -> dict:
    with conn.cursor() as curs:
        curs.execute(program_sql.GET_PROGRAMS, )
        item_list = curs.fetchall()
    item_list = utils.camelfy(item_list)
    return item_list


@app.get("/programs/<program_id>") # Resolves for a ReST endpoint
@transaction
def get_program(conn, program_id) -> dict:
    with conn.cursor() as curs:
        curs.execute(program_sql.GET_PROGRAM_BY_PROGRAM_ID, (program_id,))
        item = curs.fetchone()
    item = utils.camelfy(item)

    return item
