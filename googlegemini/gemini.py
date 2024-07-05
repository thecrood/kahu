from google.generativeai import GenerativeModel, GenerationConfig
import google.generativeai as genai

genai.configure(api_key="AIzaSyAjPjpz66zj8do7oVmoVmhuDjnDbfKsJ00")

class GeminiClient:
  """A class for interacting with the Gemini API."""

  def __init__(self):
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

    self.model = None


  def connect(self):
    """
    Establishes a connection to the Gemini model.
    """
    self.model = GenerativeModel(model_name="gemini-pro",
                              generation_config=self.generation_config,
                              safety_settings=self.safety_settings)


  def generate_text(self, text):
    """
    Generates text using the Gemini model.

    Args:
      text (str): The prompt or text to base the generation on.
      config (GenerationConfig, optional): Configuration options for generation.
        Defaults to None.

    Returns:
      str: The    self.model = None generated text response from the Gemini model.
    """
    if not self.model:
      self.connect()

    response = self.model.send_message(text=text)
    return response.text


  def chatbot(self, question, history=[],chatbot_system_context = str()):
    """
    Starts a chat session with the Gemini model.
    Args:
      history (list, optional): List of dictionaries representing conversation history.
        Each dictionary should have "text" key with message content. Defaults to [].

    Returns:
      GenerativeModel: The connected GenerativeModel instance for subsequent chat interactions.
    """

    self.model = GenerativeModel(model_name="gemini-pro",
                              generation_config=self.generation_config,
                              safety_settings=self.safety_settings)
    
    convo = self.model.start_chat(history=history)
    prompt = f"{chatbot_system_context} Question: {question}"
    response = convo.send_message(prompt)

    output_text = str()
    for candidate in response.candidates:
      output_text = candidate.content.parts[0].text
        
    return output_text

if __name__ == "__main__":
  #abc = GeminiClient()
  #result =  abc.study_section_chatbot(question="give me list best computer science engineering colleges in US",chatbot_system_context="You are a chatbot and an education consultant. Only answer the following question if it is relavate otherwise politely refused.")
  #print(result)
  #x = f"bot:{result}"
  #history = [
  #  {
  #    "role": "user",
  #    "parts": "give me list best computer science engineering colleges in US"
  #  },
  #  {
  #    "role": "model",
  #    "parts": x
  #  }
  #]
  #result =  abc.study_section_chatbot(question="give me one best college from the list", history=history)
  #print(result)
  pass