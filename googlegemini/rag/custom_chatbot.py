__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os,re
import google.generativeai as genai
from chromadb import Documents, EmbeddingFunction, Embeddings
import os
from pypdf import PdfReader
import chromadb
from typing import List


from chromadb.config import Settings



os.environ["GEMINI_API_KEY"]="AIzaSyAz6bVuHA52B46sCPsh2f_H4VirLjPiWjY"

class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom embedding function using the Gemini AI API for document retrieval.

    This class extends the EmbeddingFunction class and implements the __call__ method
    to generate embeddings for a given set of documents using the Gemini AI API.

    Parameters:
    - input (Documents): A collection of documents to be embedded.

    Returns:
    - Embeddings: Embeddings generated for the input documents.
    """
    def __call__(self, input: Documents) -> Embeddings:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("Gemini API Key not provided. Please provide GEMINI_API_KEY as an environment variable")
        genai.configure(api_key=gemini_api_key)
        model = "models/embedding-001"
        title = "Custom query"
        return genai.embed_content(model=model,
                                   content=input,
                                   task_type="retrieval_document",
                                   title=title)["embedding"]



class Custom_chatbot():
    def __init__(self) -> None:
        """
        Initializes the generation_config and safety_settings.
        """
        self.generation_config = {
          "temperature": 1,
          "top_p": 1,
          "top_k": 1,
          "max_output_tokens": 2048,
        }

        self.safety_settings = [
          {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
          },
          {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
          },
          {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
          },
          {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
          },
        ]


    def load_pdf(self, file_path):
        """
        Reads the text content from a PDF file and returns it as a single string.

        Parameters:
        - file_path (str): The file path to the PDF file.

        Returns:
        - str: The concatenated text content of all pages in the PDF.
        """
        # Logic to read pdf
        reader = PdfReader(file_path)

        # Loop over each page and store it in a variable
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        return text
    

    def split_text(self, text: str):
        """
        Splits a text string into a list of non-empty substrings based on the specified pattern.
        The "\n \n" pattern will split the document para by para
        Parameters:
        - text (str): The input text to be split.

        Returns:
        - List[str]: A list containing non-empty substrings obtained by splitting the input text.

        """
        split_text = re.split('\n \n', text)
        return [i for i in split_text if i != ""]


    def create_chroma_db(self,documents:List, path:str, name:str):
        """
        Creates a Chroma database using the provided documents, path, and collection name.

        Parameters:
        - documents: An iterable of documents to be added to the Chroma database.
        - path (str): The path where the Chroma database will be stored.
        - name (str): The name of the collection within the Chroma database.

        Returns:
        - Tuple[chromadb.Collection, str]: A tuple containing the created Chroma Collection and its name.
        """
        chroma_client = chromadb.PersistentClient(path=path,settings=Settings(anonymized_telemetry=False))
        db = chroma_client.create_collection(name=name, embedding_function=GeminiEmbeddingFunction())

        for i, d in enumerate(documents):
            db.add(documents=d, ids=str(i))

        return db, name


    def load_chroma_collection(self, path:str, name:str):
        """
        Loads an existing Chroma collection from the specified path with the given name.

        Parameters:
        - path (str): The path where the Chroma database is stored.
        - name (str): The name of the collection within the Chroma database.,settings=Settings(anonymized_telemetry=False)

        Returns:
        - chromadb.Collection: The loaded Chroma Collection.
        """
        chroma_client = chromadb.PersistentClient(path=path,settings=Settings(anonymized_telemetry=False))
        db = chroma_client.get_collection(name=name, embedding_function=GeminiEmbeddingFunction())

        return db
    

    def make_rag_prompt(self, query:str, relevant_passage:str):
        escaped = relevant_passage.replace("'", "").replace('"', "").replace("\n", " ")
        prompt = ("""You are a helpful and informative bot that answers questions using text from the reference passage included below. \
        Be sure to respond in a complete sentence, being comprehensive, including all relevant background information. \
        However, you are talking to a non-technical audience, so be sure to break down complicated concepts and \
        strike a friendly and converstional tone. \
        If the passage is irrelevant to the answer, you may ignore it.
        QUESTION: '{query}'
        PASSAGE: '{relevant_passage}'

        ANSWER:
        """).format(query=query, relevant_passage=escaped)

        return prompt


    def ask_gemini(self, prompt:str):
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("Gemini API Key not provided. Please provide GEMINI_API_KEY as an environment variable")
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-pro')
        answer = model.generate_content(prompt)
        return answer.text
    

    def chatbot(self, question, history=[],chatbot_system_context = str()):
        """
        Starts a chat session with the Gemini model.
        Args:
        history (list, optional): List of dictionaries representing conversation history.
            Each dictionary should have "text" key with message content. Defaults to [].

        Returns:
        GenerativeModel: The connected GenerativeModel instance for subsequent chat interactions.
        """

        self.model = genai.GenerativeModel(model_name="gemini-pro",
                                generation_config=self.generation_config,
                                safety_settings=self.safety_settings)
        
        convo = self.model.start_chat(history=history)
        prompt = f"{chatbot_system_context} Question: {question}"
        response = convo.send_message(prompt)

        output_text = str()
        for candidate in response.candidates:
            output_text = candidate.content.parts[0].text
            
        return output_text
    

    def get_relevant_passage(self, query, db, n_results):
        passage = db.query(query_texts=[query], n_results=n_results)['documents'][0]
        return passage


    def generate_answer(self, db, query,history=list(),chatbot_system_context=""):
        #retrieve top 3 relevant text chunks
        relevant_text = self.get_relevant_passage(query,db,n_results=3)
        #prompt = self.make_rag_prompt(query, 
        #                        relevant_passage="".join(relevant_text)) # joining the relevant chunks to create a single passage
        #answer = self.ask_gemini(prompt)
        history.extend([{"role":"user",
                 "parts":relevant_text
                  },
                {"role":"model",
                 "parts":"I understand the context of your StudySection inquiry. However, I am also capable of answering a broader range of education-related questions."}])
        
       
        answer = self.chatbot(question=query,history=history,chatbot_system_context=chatbot_system_context)
        return answer



    def load_custom_data(self,file_path,vector_db_path,db_name):
        '''
        A pipeline that loads the data(ingestion), processes it, and then stores it. You need to index the documents only once
        '''
        pdf_text = self.load_pdf(file_path=file_path)
        pdf_chunked_text = self.split_text(pdf_text)
        db,name = self.create_chroma_db(documents=pdf_chunked_text, 
                          path=vector_db_path, #replace with your path
                          name=db_name)
        
        print(f'{name} vector database is created')

    
    def retrieval_n_generation(self,vector_db_path,vector_db_name,query,history,chatbot_system_context):
        db= self.load_chroma_collection(path=vector_db_path, name=vector_db_name)
        answer = self.generate_answer(db,query,history,chatbot_system_context)
        answer = answer.replace("Answer:","")
        return answer
        






        
        
        
if __name__ == "__main__":
    #chatbot = Custom_chatbot()
    #chatbot.load_custom_data(file_path="/home/webner/Downloads/FAQ - Study Section - Sheet1 (2).pdf",vector_db_path=os.getcwd()+"/googlegemini/rag/contents/",db_name="study-section")
    #chatbot.retrieval_n_generation("/home/webner/Documents/projects/DocReader/chatbot_3/rag/contents/","study-section","who are you.")
    pass