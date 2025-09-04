from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
import logging
from AppShared import db_utils, utils
import class_sql
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

@app.get("/classes")
@transaction
def list_classes(conn) -> dict:
    with conn.cursor() as curs:
        curs.execute(class_sql.GET_CLASSES)
        item_list = curs.fetchall()
    item_list = utils.camelfy(item_list)
    return item_list


@app.get("/classes/<class_id>") # Resolves for a ReST endpoint
@transaction
def get_class(conn, class_id) -> dict:
    with conn.cursor() as curs:
        curs.execute(class_sql.GET_CLASS_BY_CLASS_ID, {"class_id": class_id})
        item = curs.fetchone()
    item = utils.camelfy(item)
    return item


@app.delete("/classes/<class_id>")
@transaction
def delete_class(conn, class_id) -> dict:
    with conn.cursor() as curs:
        curs.execute(class_sql.DELETE_CLASS, {"class_id": class_id})
    return {'result': 'success'}

