import logging
from fastapi import FastAPI, File, UploadFile
from io import BytesIO
import pandas as pd
from mangum import Mangum
import zipfile

import json
import boto3
import io

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
s3_client = boto3.client("s3")

@app.post("/batch", tags=["Batch"], summary="Create Batch", description="Upload a file (edt).")
async def create_batch(edt: UploadFile = File(...)):
    s3_bucket = 'moneo-serverless-bucket'

    # Validate file type (optional, based on your requirements)
    if not edt.filename.endswith((".xlsx", ".xls", ".csv")):
        logger.error("Invalid file format. The file must be in .csv, .xls or .xlsx format")
        return {"error": "The file must be in .csv, .xls or .xlsx format"}

    try:

        # Read the content of the file
        content = await edt.read()

        # Load the content into a BytesIO object
        file_obj = BytesIO(content)

        # Read the Excel content as a Pandas DataFrame
        df = pd.read_csv(file_obj)

        # Set option to display all columns when printing the DataFrame
        pd.set_option('display.max_columns', None)

        # Print the first rows of the DataFrame
        logger.info("First rows of the DataFrame:")
        logger.info(df.head())
        print("print first rows:", df.head())
        print("Print df", df)

        # Validate column datatype
        # Define expected column names and their data types
        expected_columns = {
            "Top_Entity": str,
            "Legal_Entity": str,
            "Portfolio_Name": str,
            "Asset_ID": str,
            "NAIC_Asset_Type": str,
            "Account_Number": str,
            "Entry_Date": str,
            "Reporting_Month": str,
            "Entry_Amount_Debit": float,
            "Entry_Amount_Credit": float,
            "Currency_Code": str,
            "Financial_Statement_Grouping": str,
            "Financial_Statement_Sub_Grouping": str,
            "Dynamic_Validation_Grouping": str,
            "Dynamic_Validation_Sub_Grouping": str
        }
        
        # Validate each column against expected datatype
        errors = {}
        for column, dtype in expected_columns.items():
            try:
                df[column] = df[column].astype(dtype)
            except ValueError:
                errors[column] = f"Invalid datatype for column {column}"

        if errors:
            return {"error validating columns and data": errors}
        
        logger.info(f"File received and processed successfully: {edt.filename}, content_length: {len(content)}")

        # Upload data to s3
        s3_client.upload_fileobj(edt.file, s3_bucket, f"uploaded_files/{edt.filename}")
        
        logger.info(f"File uploaded to S3 successfully: {edt.filename}")
        return {"message": "File uploaded to S3 successfully", "file_name": edt.filename}

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return {"error": str(e)}

handler = Mangum(app)

"""
    from fastapi import FastAPI, Request
    from fastapi.params import Body
    from mangum import Mangum
    from pydantic import BaseModel

    app = FastAPI(title="N5", version="1.0", root_path="/dev/")
    posts = []

    class Post(BaseModel):
        title: str
        content: str

    @app.get("/moneoget")
    async def read_root_get():
        return {"message": "FastAPI running in a lambda funcin"}

    @app.get("/list-posts")
    async def lists_post_get():
        return {"message": f"{posts}"}

    @app.post("/moneopost")
    async def read_root_post():
        return {"message": "This is a post method yeah!"}

    @app.post("/upload-data")
    async def upload_data_post(data: Post):
        posts.append(data.dict())
        return {"message": f"Post created: {data.title}, {data.content}"}

    @app.post("/upload-csv")
    async def upload_csv_file(request: Request):
        form = await request.form()
        
        file = form.get("file")
        if file is None:
            raise HTTPException(status_code=400, detail="No file attached")
        
        contents = await file.read()
        return {"filename": file.filename, "file_contents": contents}

    handler = Mangum(app)
"""

