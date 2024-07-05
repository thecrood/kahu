from fastapi import APIRouter, status
from fastapi.responses import ORJSONResponse
from typing import Optional
from app.schemas import Chatbot
from googlegemini.gemini import GeminiClient
import mysql.connector
from decimal import Decimal
import json

from langchain_openai.chat_models import AzureChatOpenAI
from langchain_community.utilities import SQLDatabase
from pprint import pprint
from langchain.chains import create_sql_query_chain
from langchain_google_genai import ChatGoogleGenerativeAI
import os.path
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
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

router = APIRouter()

os.environ["AZURE_OPENAI_API_KEY"] = "54564b4e19b34f4183af8d6ececee406"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://docreadertestai.openai.azure.com/"
os.environ["AZURE_OPENAI_API_VERSION"] = "2023-05-15"
os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"] = "GPT-35-turbo-16K-model"


def create_sql_connection():
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "al3_2019.db")
    db_path = 'sqlite:////' + db_path
    # db_path = 'sqlite:////' + r'/home/webner/Documents/projects/chatbot/winsurtechaichatbot/app/routes/al3_2019.db'
    print(db_path)
    db = SQLDatabase.from_uri(db_path)
    return db
    
    
    mydb = mysql.connector.connect(
    host="31.220.82.114",
    user="testdb",
    password="5Y0:|?^!YlBOP",
    database="dummyschema"
    )
    
    mycursor = mydb.cursor()
    
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    
    return myresult

def get_table_details():
            # Read the CSV file into a DataFrame
            table_description = pd.read_csv("database_table_descriptions.csv")
            # print(table_description)
            table_docs = []
            
            # Iterate over the DataFrame rows to create Document objects
            table_details = ""
            for index, row in table_description.iterrows():
                # print(row["Table"])
                table_details = table_details + "Table Name:" + row["Table"] + "\n" + "Table Description:" + row['Description'] + "\n\n"
                
            return table_details




def get_result_from_database(question):
    
    db = create_sql_connection()
    
    llm = AzureChatOpenAI(
            openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        )
    
    lob_name_full_form = [
        {'Homeowners': 'HOME'},
        {'Automobile':'AUTOP'},
        {'Property','PROP'}   
    ]
    
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
                "input": "Give me the list of lob present?",
                "query": "select DISTINCT(lob_name) from lob_group_hierarchy"
            },
            {
                "input": "what are various group code under lob DFIRE",
                "query": "select group_code from lob_group_hierarchy where lob_name = 'DFIRE'"
            },
            {
                "input": "how many group_code are present under lob name Home?",
                "query": "select count(group_code) from lob_group_hierarchy where lob_name = 'HOME';"
            },
            {
                "input": "Give various al3 group with their group name, definition and length of group?",
                "query": "Select AL3Group, GroupName, DefinitionText, GroupLength from Groups"
            },
            {
                "input": "Give length and definition of al3 elements whose group code is 9COC",
                "query": "select AL3Length, AL3DefinitionText from Elements where AL3Group = '9COC"
            },
            {
                "input": "what is 5BIS",
                "query": "Select  GroupName, DefinitionText from Groups where AL3Group = '5BIS'"
            },
            {
                "input": "what is message sequence number in message header group",
                "query": "Select AL3DefinitionText from Elements where description = 'Message Sequence Number' and AL3Group = (Select AL3Group from Groups where GroupName = 'Message Header Group')"
            },
            {
                "input": "elements present in al3 group name Basic Policy Information Group",
                "query": "select description from Elements where AL3Group = (Select AL3Group from Groups where GroupName = 'Basic Policy Information Group') order by Element"
            },
            {
                "input": "what is message header group",
                "query": "select DefinitionText from Groups where GroupName = 'Message Header Group'"
            },
            {
                "input": "What are various mandatory elements",
                "query": "select GroupElement from Elements where Presence = 'M'"
            },
            {
                "input": "elements of Attachments Group",
                "query": "select description from Elements where AL3Group = (Select AL3Group from Groups where GroupName = 'Attachments Group') order by Element"
            },
            {
                "input": "what is AL3Group 2TRG",
                "query": "Select GroupName, DefinitionText from Groups where AL3Group = '2TRG'"
            },
            {
                "input": "what is Group Name Distribution Partner Information Group or explain distribution partner information group",
                "query": "select DefinitionText from Groups where GroupName = 'Distribution Partner Information Group'"
            },
            {
                "input": "what are various Al3 group code present in 'Automobile' or 'AUTOP'",
                "query": "select group_code from lob_group_hierarchy where lob_name = 'AUTOP'"
            },
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
    

@router.post("/al3todb/chatbot")
async def study_section_chatbot(chat_query:Chatbot=Chatbot()):
    try:
        chat_query = {**chat_query.model_dump()}
        question = chat_query['question']
        history = chat_query['history']

        if question == "":
            return ORJSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                    content={"http_code" : status.HTTP_400_BAD_REQUEST,
                                        "status": "failed",
                                        "message": "question is missing"})
        
        if 'delete' in question.lower() or 'update' in question.lower() or 'insert' in question.lower() or 'drop' in question.lower() or 'truncate' in question.lower() or 'alter' in question.lower():
            return ORJSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                    content={"http_code" : status.HTTP_400_BAD_REQUEST,
                                        "status": "failed",
                                        "message": "operation not allowerd is missing"})
            
        
        query_output = get_result_from_database(question)
        print("query_output", query_output)
        
        chat_obj = GeminiClient()
        
        chatbot_context = "check if the question or provided text contains proper data or not. if proper response is present then return 'present' otherwise return 'empty'"
        # chatbot_context = "The question given contains the data from some table in database which can be text or records. If the question contains the output from table return 'present' otherwise for non database result return 'empty'"
        
        bot_response = chat_obj.chatbot(question=str(query_output),history=history,chatbot_system_context=chatbot_context)
        
        print("bot_response", bot_response)
        
        if bot_response == 'present' or bot_response == 'Present':
            return json.dumps({"text": f"{query_output}"})
        else:
            chatbot_system_context = '''You are a multilingual chatbot and an insurance agent and ACORD and AL3 consultant created and trained by Winsurtech (an InsurTech company, they develop software and services specifically for the 
            insurance industry https://winsurtech.com/. They won ACORD Insurance Awards in both 2022 and 2023. Winsurtech products are - AL3 Parser, AL3 Creator, Docreader, FormCruise, Study Section, IVANS Downloader, AL3 Web Viewer, AL3 Desktop Viewer). Do not give any 
            information for question related to date, day, time etc. and never return a blank response, 
            always return something as output and Only answer the following question in proper format otherwise politely refused
            '''
            
            # chatbot_database_context = """You are an expert in converting English questions to SQL query! 
            # The SQL database dummyschema has the name Customers and has the following column and datatype - CustomerID int , CustomerName varchar, 
            # ContactName varchar, PostalCode int and Country varchar \n\n
            # For Example \n Example 1 - How many entries of records are present?, 
            # the SQL command will be something like this SELECT COUNT(*) FROM dummyschema.Customers ;
            # \nExample 2 - Tell me all the Customers having country Mexico?, 
            # the SQL command will be something like this SELECT * FROM dummyschema.Customers 
            # where Country="Mexico"; 
            # also do not accept delete, update, alter, drop or any other similar query which can affect data and
            # also the sql code should not have ``` in beginning or end and sql word in output
            # """
            
            # chat_obj = GeminiClient()
            
            # chatbot_query_filter = "We have two roles \n 1. General query" + chatbot_system_context + "and 2. Database query" + chatbot_database_context + "You need to identify if the question is related to role 1 or role 2 and return string role1 or role2 as output depending upon analysis"
            # query_filter_response = chat_obj.chatbot(question=question,history=history,chatbot_system_context=chatbot_query_filter)
            
            # if "role2" in query_filter_response.lower() or "role 2" in query_filter_response.lower():
            #     chatbot_context = chatbot_database_context
            # else:
            # chatbot_context = chatbot_system_context
                
            bot_response = chat_obj.chatbot(question=question,history=history,chatbot_system_context=chatbot_system_context)
            
            # if "role2" in query_filter_response.lower() or "role 2" in query_filter_response.lower():
            #     if "update" in bot_response.lower() or "delete" in bot_response.lower() or "alter" in bot_response.lower() or "drop" in bot_response.lower():
            #         bot_response = "Operation not allowed due to applied restrictions"
            #     else:
            # bot_response = get_sql_output(bot_response)
                
            return json.dumps({"text": f"{bot_response}"})
        return ORJSONResponse(status_code=status.HTTP_200_OK,
                              content={'http_code': status.HTTP_200_OK,
                              "status": "successful", 
                              "output": bot_response})
        
    except Exception as e:
        return ORJSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              content={'http_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                              "status": "failed", 
                              "message": "Internal Server Error",
                              "error":str(e)})