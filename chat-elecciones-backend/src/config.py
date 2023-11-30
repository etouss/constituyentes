import os
import boto3
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Databases: local, chatdata, elections
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_database = os.getenv("POSTGRES_DB")
db_host = os.getenv("POSTGRES_HOST")
db_port = os.getenv("POSTGRES_PORT")

db_do_host = os.getenv("DO_HOST")
db_do_port = os.getenv("DO_PORT")

db_user_chatdata = os.getenv("PG_USER_CHATDATA")
db_password_chatdata = os.getenv("PG_PASSWORD_CHATDATA")
db_database_chatdata = os.getenv("PG_DB_CHATDATA")

db_user_elections = os.getenv("PG_USER_ELECTIONS")
db_password_elections = os.getenv("PG_PASSWORD_ELECTIONS")
db_database_elections = os.getenv("PG_DB_ELECTIONS")

SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
)

SQLALCHEMY_CHATDATA_URI = (
    f"postgresql://{db_user_chatdata}:{db_password_chatdata}@{db_do_host}:{db_do_port}/{db_database_chatdata}"
)

SQLALCHEMY_ELECTIONS_URI = (
    f"postgresql://{db_user_elections}:{db_password_elections}@{db_do_host}:{db_do_port}/{db_database_elections}"
)

engine_local = create_engine(SQLALCHEMY_DATABASE_URI)
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine_local)

engine_chatdata = create_engine(SQLALCHEMY_CHATDATA_URI)
session_chatdata = sessionmaker(autocommit=False, autoflush=False, bind=engine_chatdata)

engine_elections = create_engine(SQLALCHEMY_ELECTIONS_URI)
session_elections = sessionmaker(autocommit=False, autoflush=False, bind=engine_elections)

# DO Spaces
DO_SPACES_KEY = os.environ.get("DO_SPACES_KEY")
DO_SPACES_SECRET = os.environ.get("DO_SPACES_SECRET")
DO_SPACES_REGION = os.getenv("DO_SPACES_REGION")
DO_SPACES_BUCKET = os.getenv("DO_SPACES_BUCKET")

session = boto3.session.Session()
client = session.client("s3",
    region_name=os.getenv("DO_SPACES_REGION"),
    endpoint_url=f"https://{DO_SPACES_REGION}.digitaloceanspaces.com",
    aws_access_key_id=DO_SPACES_KEY,
    aws_secret_access_key=DO_SPACES_SECRET
)

def download_embeddings_file(file_name, local_file_path):
    client.download_file(DO_SPACES_BUCKET, file_name, local_file_path)


def get_vector_list():
    download_embeddings_file("embeddings/embeddings.npy", "embeddings.npy")
    vector_list = np.load("embeddings.npy")
    return vector_list
