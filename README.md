# Database Connections: Lesson 3

Let me say this up front. I know that connecting directly to a relational database from a lambda is not always ideal. There are other solutions that handle 
the horizontal scaling of lambdas better like using DynamoDB instead of RDS or connecting via RDS Proxy. I wanted to 
demonstrate a simple, efficient and robust pattern for connecting to RDS from a lambda for these reasons. 
1. Many people just want a simple API in front of a relational database and will not be scaling  
   enough to justify the costs of RDS Proxy.
2. Aurora Serverless is a relational database that automatically scales and is a legitimate choice for many use cases
   that need persistence with lambdas without the need for RDS Proxy.
3. Often people who are trying to do something with lambda for the first time have enough to learn without having to 
learn the nuances of DynamoDB, and can't afford to have an RDS instance always running. This project and the [simple-database](https://github.com/SimpleServerless/simple-database)
project give those folks a way of getting started with lambda and an RDS database with very low AWS costs and a working
template to help them avoid some common landmines.
4. I've actually been using these patterns on high volume production systems for years. If you put a little thought into
timeouts and provisioning it works just fine for a lot of use cases and is one of the simplest ways to build an API.
  

# Objectives
- Demonstrate how to create and cache database connections in a lambda. 
- Demonstrate how to use a decorator in Python to inject datbase connection into a function
- Demonstrate how to use a decorator in Python to wrap a function with a transaction

# What's in this repo
This repo is a companion to **Lesson 3** in the "Simple Serverless" series and future lessons will build on the tools and patterns used here.
I hope you find something here helpful, and please give this repo a star if you do. Thanks for checking it out.

This repo builds on the patterns used in [Dynamic Routing: Lesson 2](https://github.com/SimpleServerless/dynamic-routing) 
that uses decorators to map REST and GrqphQL endpoints to functions in lambdas but also leverages CDK to scan the lambda
for decorators and automatically generate API Gateway (REST) or AppSync (GraphQL) endpoints during deployment.

You can use CDK and the included `app.py` file to deploy a fully functional API to AWS. 
I was careful to favor resources that are only "pay for what you use" so there should be little or no reoccurring costs for this deployment.

I also use this repo as a toolbox of tricks I've learned over the years to make developing lambdas fast and easy. 

You will find in this repo:
- The `@transaction` decorator that will wrap a function with a transaction and inject a cached database connection 
  that returns results as a list of dictionaries. Successful executions are automatically committed and failed executions 
  are automatically rolled back.
- A single CDK file (app.py) that will scan lambda_function.py for decorators ex: `@router.rest("GET", "/students")` and 
  automatically generate API Gateway (REST) or AppSync (GraphQL) endpoints. See [Dynamic Routing: Lesson 2](https://github.com/SimpleServerless/dynamic-routing)
- All the infrastructure as code needed to deploy fully functional APIs via SAM which is an AWS extension of CloudFormation
- A simple script (`run_local.py`) that makes it easy to iterate and debug locally
- Commands to invoke a deployed lambda and tail its logs in realtime (`make invoke`, `make tail`)


# Example

Note: because I ran out of talent the `@transacton` decorator has to be the last decorator before the function definition.

```
@router.rest("GET", "/students")
@transaction
def list_students(conn, args: dict) -> dict:
    with conn.cursor() as curs:
        curs.execute(sql.GET_STUDENTS, )
        item_list = curs.fetchall()
    return item_list
```

This wraps the function in a decorator that lazy loads and caches the connection and handles the sql tranaction appropriately.
The connection also uses the `RealDictCursor` so all results are returned as dictionaries. This complements lambda nicely
as it allows you to return the results directly and let lambda convert the dictionary to json.

You can find this magic in `db_utils.py`

```
# db_utils.py

@contextmanager
def transaction_wrapper(name="transaction_wrapper", **kwargs):
    global connection, db_user, db_password

    # Lazy load credentials. Should only happen on cold start
    if db_user is None:
        db_user, db_password = get_db_credentials()
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
```

# Requirements

- Python 3.8
- Pip 3
- AWS CLI: [Install](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- CDK: [Getting started with CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)
- make
- An RDS postgresql database on your VPC to connnect to
- An AWS account with permissions to deploy Lambda, API Gateway, AppSync 
- An S3 Bucket for uploading the lambda deployments as defined in the `S3_BUCKET` variable in the make file.
and other resources they depend on.
- A shell configured with your AWS credentials AWS_DEFAULT_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY... 
  [docs](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)

# Database Setup
- This project assumes it's using a Postgres database
- It's a best practice to have your database on a private subnet and to only allow connections to it from your VPC.
It's also a best practice to control access to your database with VPC security groups. I've published a repo for deploying 
an Aurora Serverless RDS database here [simple-database](https://github.com/SimpleServerless/simple-database). This deployment
is configured to shut the database down after it's been idle for one hour keeping costs down if you're just prototyping.
This deployment will also exports the database url, name, and allowed security group that `app.py` in this repo imports
for its configuration. Many people have asked me to provide and example of a configuration like this, but if you 
already have a database setup and don't need this you can change the relevant lines in app.py to whatever values are appropriate:
```
# app.py
# Change these lines to the appripriate values for your project
db_host = core.Fn.import_value(f"simple-serverless-database-{stage}-Host")
db_name = core.Fn.import_value(f"simple-serverless-database-{stage}-Name")
app_security_group_id = core.Fn.import_value(f"simple-serverless-database-{stage}-AppSGId")
```
- Create a plain text json secret in secrets manager for the database credentials. The value should look 
like `{"username": "my-db-user","password": "my-db-password"}` and the name should be `simple-serverless/db-credentials`
or whatever you want to define it as in db_utils.get_db_credentials().
- Change the vpcId in the environment dictionary in app.py to the appropriate values for the environment you're deploying to.
```
environment: dict = {'dev': {
                             'logLevel': 'DEBUG',
                             'vpcId': 'vpc-myvpcid'
                             }
                     }
```


# Deploy
```
git clone git@github.com:SimpleServerless/simple-db-connection.git
cd simple-db-connection
make deploy
```

# Files Explanation

**app.py:** All the infrastructure as code needed to deploy this recipe to AWS. This file contains the code that does 
the actual dynamic generation of endpoints based on the decorators found in lambda_function

**Makefile:** Make targets for deploying, testing and iterating. See [Make Targets](#make-targets) for more information.

**run_local.py:** Helper script for testing and iterating locally in a shell or IDE. 
You can run this script in an IDE to execute lambda_function.handler locally, set break points...

**/src**

&nbsp;&nbsp;&nbsp;&nbsp;**db_utils.py:** Contains the magic for this project. 

&nbsp;&nbsp;&nbsp;&nbsp;**lambda_function.py:** Contains the lambda handler and all CRUD or business logic functions the endpoints are routed to.

&nbsp;&nbsp;&nbsp;&nbsp;**requirements.txt:** Contains a list of any dependancies that needs to be included in the deploy.

&nbsp;&nbsp;&nbsp;&nbsp;**schema.graphql:** GraphQL schema only used if grqphQL routes are declared

&nbsp;&nbsp;&nbsp;&nbsp;**utils.py:** Contains supporting functions for lambda_handler.py


# Make Targets
**clean:** Removes artifacts that are created by testing and deploying

**build:** Uses src/requirements.txt to prepare target appropriate (manylinux1_x86_64) dependencies for deployment

**deploy:** Uses CDK and `app.py` to deploy the function and supporting infrastructure to AWS.

**synth:** Uses CDK and `app.py` to generate and output a CloudFormation template that represents the deployment. This can be
useful for iterating on changes to `app.py` without waiting for an actual deploy to see if it's valid.

**invoke:** Uses the AWS CLI to invoke the deployed function.

**run-local:** Uses run_local.py to execute the handler locally. This target demonstrates
how run_local.py can be used as a wrapper to run and debug the function in a shell or from an IDE.

**tail:** Uses the AWS CLI to tail the logs of the deployed function in realtime.



# Iterate in a local environment
You'll need to have your AWS credentials set up in your shell to access AWS resources like SecretsManager. [docs](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)

The `run_local` make target demonstrates how to use the run_local.py script to iterate locally, or as something you can 
run in an IDE allowing you so set breakpoints and debug. 

# What if I only want and example of GraphQL instead of REST?
This project is focused on connecting a lambda to a relational database, but you could easily deploy a 
GraphQL api instead. You can find everything you need to do that here [Dynamic Routing: Lesson 2](https://github.com/SimpleServerless/dynamic-routing)

