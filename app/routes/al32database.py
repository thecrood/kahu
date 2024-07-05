from fastapi import APIRouter, status
from fastapi.responses import ORJSONResponse
from typing import Optional
from app.schemas import Chatbot
from googlegemini.gemini import GeminiClient
import mysql.connector
from decimal import Decimal
import json

from langchain_openai.chat_models import AzureChatOpenAI
# from langchain_openai import ChatOpenAI
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_openai import OpenAIEmbeddings
from langchain_community.utilities import SQLDatabase
from pprint import pprint
from langchain.chains import create_sql_query_chain
from langchain_google_genai import ChatGoogleGenerativeAI
import os.path
from langchain_community.tools.sql_database.tool import SQLDatabase
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder,FewShotChatMessagePromptTemplate,PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import AzureOpenAIEmbeddings
import google.generativeai as genai
from langchain.chains.openai_tools import create_extraction_chain_pydantic
from operator import itemgetter
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
import pandas as pd
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ArgumentError

router = APIRouter()

os.environ["AZURE_OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""
os.environ["AZURE_OPENAI_API_VERSION"] = "2023-05-15"
os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"] = "GPT-35-turbo-16K-model"



# MySQL database connection configuration
def create_sql_connection():
    user = ""
    password = ""
    host = ""
    port = "3306"
    dbname = ""
    
    try:
        db = SQLDatabase.from_uri(f"mysql+pymysql://{user}:{password}@{host}/{dbname}")
        return db
    except ArgumentError as e:
        print(f"Error: Invalid SQLAlchemy URI: {e}")
    except Exception as e:
        print(f"Error: Failed to connect to database: {e}")

import csv
# Function to fetch table details from a CSV file
def get_table_details():
    # First, preprocess the CSV file to handle inconsistent lines
    cleaned_lines = []
    with open("database_table_descriptions.csv", 'r') as file:
        reader = csv.reader(file)
        for line in reader:
            if len(line) == 2:  # Ensure the line has exactly 2 fields
                cleaned_lines.append(line)
            else:
                print(f"Skipping malformed line: {line}")

    # Convert the cleaned lines back to a DataFrame
    table_description = pd.DataFrame(cleaned_lines, columns=["Table", "Description"])

    # Generate the table details string
    table_details = ""
    for index, row in table_description.iterrows():
        table_details += f"Table Name: {row['Table']}\nTable Description: {row['Description']}\n\n"
    return table_details

# Function to interact with the database and chat models
def get_result_from_database(question):
    
    db = create_sql_connection()
    
    llm = AzureChatOpenAI(
            openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        )
    
    execute_query = QuerySQLDataBaseTool(db = db)
    
    answer_prompt = PromptTemplate.from_template(
            """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

        Question: {question}
        SQL Query: {query}
        SQL Result: {result}
        Answer: """
        )
        
    rephrase_answer = answer_prompt | llm | StrOutputParser()
    
    examples = [
            {
                "input": "policies from policies table?",
                "query": "SELECT * FROM policies WHERE id = '0004111de9394524925263107ed67005';"
            },
            {
                 "input": "all records from policies table?",
                 "query": "SELECT * FROM policies;"
            },
            {
                "input": "all records from policies table where lob is Personal package?",
                 "query": "SELECT * FROM policies WHERE line_of_business_code = 'Personal package';" 
            }
        ]
    
    example_prompt = ChatPromptTemplate.from_messages(
            [
                ("human", "{input}\nSQLQuery:"),
                ("ai", "{query}"),
            ]
        )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=examples,
            # input_variables=["input","top_k"],
            input_variables=["input"],
        )
    
    vectorstore = Chroma()
    vectorstore.delete_collection()
    
    embeddings = AzureOpenAIEmbeddings(
                azure_deployment="docreaderTextEmbedding",
                openai_api_version="2023-05-15",
                # api_key="54564b4e19b34f4183af8d6ececee406",
                # azure_endpoint="https://docreadertestai2.openai.azure.com/",
                # openai_api_type="azure"
            )
    
    example_selector = SemanticSimilarityExampleSelector.from_examples(
            examples,
            embeddings,
            vectorstore,
            k=2,
            input_keys=["input"],
        )
    
    few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            example_selector=example_selector,
            input_variables=["input","top_k"],
        )

    final_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a MySQL expert. Given an input question, create a syntactically correct MySQL query to run. Unless otherwise specificed.\n\nHere is the relevant table info: {table_info}\n\nBelow are a number of examples of questions and their corresponding SQL queries."),
                few_shot_prompt,
                ("human", "{input}"),
            ]
        )
    
    generate_query = create_sql_query_chain(llm, db,final_prompt)
    
    #temporary -- will comment later
    # query = generate_query.invoke({"question": question})
    # print("query", query)
        
    class Table(BaseModel):
            """Table in SQL database."""
            name: str = Field(description="Name of table in SQL database.")

    table_details = get_table_details()
    # print(table_details)
    
    table_details_prompt = f"""Return the names of ALL the SQL tables that MIGHT be relevant to the user question. \
    The tables are:
    {table_details}
    
    Remember to include ALL POTENTIALLY RELEVANT tables, even if you're not sure that they're needed."""
    
    
    create_extraction_chain_pydantic(Table, llm, system_message=table_details_prompt)
    
    def get_tables(tables: List[Table]) -> List[str]:
            tables  = [table.name for table in tables]
            return tables
    
    select_table = {"input": itemgetter("question")} | create_extraction_chain_pydantic(Table, llm, system_message=table_details_prompt) | get_tables
    
    chain = (
            RunnablePassthrough.assign(table_names_to_use=select_table) | 
            RunnablePassthrough.assign(query=generate_query).assign(
                result=itemgetter("query") | execute_query
            )
            | rephrase_answer
    )
    
    query_output = chain.invoke({"question": question})
    return query_output

    
# FastAPI endpoint to handle POST requests
@router.post("/al3todatabase/chatbot")
async def study_section_chatbot(chat_query: Chatbot = Chatbot()):
    try:
        chat_query = {**chat_query.model_dump()}
        question = chat_query['question']
        history = chat_query['history']
        
        if question == "":
            return ORJSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                  content={"http_code": status.HTTP_400_BAD_REQUEST,
                                           "status": "failed",
                                           "message": "question is missing"})
        
        # Validate if the question contains restricted SQL keywords
        if any(keyword in question.lower() for keyword in ['delete', 'update', 'insert', 'drop', 'truncate', 'alter']):
            return ORJSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                  content={"http_code": status.HTTP_400_BAD_REQUEST,
                                           "status": "failed",
                                           "message": "operation not allowed"})
        
        query_output = get_result_from_database(question)
        
        chat_obj = GeminiClient()
        chatbot_context = "check if the question or provided text contains proper data or not. if proper response is present then return 'present' otherwise return 'empty'"
        
        bot_response = chat_obj.chatbot(question=str(query_output), history=history, chatbot_system_context=chatbot_context)
        
        if bot_response.lower() == 'present':
            return ORJSONResponse(status_code=status.HTTP_200_OK,
                                  content={"text": f"{query_output}"})
        else:
            chatbot_system_context = '''
            You are a multilingual chatbot and an insurance agent and ACORD and AL3 consultant created and trained by Winsurtech 
            (an InsurTech company, they develop software and services specifically for the insurance industry 
            https://winsurtech.com/. They won ACORD Insurance Awards in both 2022 and 2023. Winsurtech products are - AL3 Parser, 
            AL3 Creator, Docreader, FormCruise, Study Section, IVANS Downloader, AL3 Web Viewer, AL3 Desktop Viewer). Do not give any 
            information for question related to date, day, time etc. and never return a blank response, always return something as 
            output and Only answer the following question in proper format otherwise politely refused
            '''
            
            bot_response = chat_obj.chatbot(question=question, history=history, chatbot_system_context=chatbot_system_context)
            
            return ORJSONResponse(status_code=status.HTTP_200_OK,
                                  content={"text": f"{bot_response}"})
    
    except Exception as e:
        return ORJSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              content={"http_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                                       "status": "failed",
                                       "message": "Internal Server Error",
                                       "error": str(e)})