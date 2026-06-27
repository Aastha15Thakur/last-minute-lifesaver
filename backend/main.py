import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

app = FastAPI()

# Crucial for Hackathons: Allow the Next.js frontend to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the official Google GenAI Client
# Ensure you run 'export GEMINI_API_KEY="your_actual_key"' in your terminal first!
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("⚠️ WARNING: GEMINI_API_KEY environment variable is missing!")

client = genai.Client()

class TaskRequest(BaseModel):
    task_title: str

@app.get("/api/health")
def health_check():
    return {"status": "Backend is alive!"}

@app.post("/api/test-ai")
def test_ai(payload: TaskRequest):
    try:
        # Prompt telling Gemini exactly what its identity is for this hackathon
        prompt = f"""
        You are the 'Last-Minute Life Saver' agent. 
        The user is struggling with procrastination on this task: '{payload.task_title}'.
        Give them a 2-sentence response:
        1. Break down the immediate first step they need to do right now.
        2. Give them a high-energy, urgent motivation kick.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        return {"ai_response": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API Error: {str(e)}")