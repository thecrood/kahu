from fastapi import FastAPI
from .routes import study_section, al3_to_db, al32database
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

templates = Jinja2Templates(directory="GPTUI")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Render the HTML template
    print("request", request)
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/al32db", response_class=HTMLResponse)
async def read_root(request: Request):
    # Render the HTML template
    print("request", request)
    return templates.TemplateResponse("al32db.html", {"request": request})

class ChatRequest(BaseModel):
    userText: str

class ChatResponse(BaseModel):
    text: str

@app.post("/api/chat")
async def get_chat_response(request: ChatRequest):
    # This is a placeholder for actual logic to get a response from your chatbot
    # You would replace this with the logic for interacting with your chatbot model
    # For example, if you have a separate service that handles the chatbot logic,
    # you would make a request to that service here.
    # In this example, we'll just echo back the user's input.
    print("the function code be like")
    return {"text": f"You said: {request.userText}"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(study_section.router)
app.include_router(al3_to_db.router)
app.include_router(al32database.router)                    