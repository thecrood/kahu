from fastapi import APIRouter, status
from fastapi.responses import ORJSONResponse
from typing import Optional
from app.schemas import Chatbot
from googlegemini.gemini import GeminiClient
from googlegemini.rag.custom_chatbot import Custom_chatbot
import os


router = APIRouter()

@router.post("/study-section/chatbot")
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
        
        chatbot_system_context = "You are a chatbot and an education consultant. Only answer the following question if it is relavate otherwise politely refused."
        #chat_obj = GeminiClient()
        #bot_response = chat_obj.chatbot(question=question,history=history,chatbot_system_context=chatbot_system_context)

        vector_db_path = os.getcwd() + os.sep + "googlegemini" + os.sep + "rag" + os.sep + "contents" + os.sep
        chat_obj = Custom_chatbot()
        bot_response = chat_obj.retrieval_n_generation(vector_db_path=vector_db_path,vector_db_name="study-section",query=question,history=history,chatbot_system_context=chatbot_system_context)
        
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