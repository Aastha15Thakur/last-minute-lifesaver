import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from typing import List
from database import get_db_connection
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

class TaskRequest(BaseModel):
    task_title: str
    deadline: str
    difficulty: str

# --- UPDATED PYDANTIC SCHEMA FOR GEMINI ---
class AISubtaskSchema(BaseModel):
    priority: str = Field(
        description="Calculated priority rating ('Low', 'Medium', 'High', or 'Critical') based on the absolute deadline closeness."
    )
    reason: str = Field(
        description="A 1-sentence analytical justification of why this priority was assigned and how tight the window is."
    )
    estimated_hours: float = Field(
        description="Total estimated active work hours required to realistically finish all subtasks combined."
    )
    subtasks: List[str] = Field(
        description="A list of 3-5 immediate, highly specific, actionable subtasks to complete the main goal."
    )

@app.get("/api/health")
def health_check():
    return {"status": "Backend is alive!"}

@app.get("/api/debug-tasks")
def debug_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    tasks = cursor.execute("SELECT * FROM tasks").fetchall()
    subtasks = cursor.execute("SELECT * FROM subtasks").fetchall()
    conn.close()
    return {
        "stored_tasks": [dict(t) for t in tasks],
        "stored_subtasks": [dict(s) for s in subtasks]
    }

@app.get("/api/dashboard")
def get_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    task = cursor.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT 1").fetchone()
    if not task:
        conn.close()
        return {"task": None, "subtasks": []}
    subtasks = cursor.execute("SELECT * FROM subtasks WHERE task_id = ?", (task["id"],)).fetchall()
    conn.close()
    return {
        "task": dict(task),
        "subtasks": [dict(s) for s in subtasks]
    }

class ToggleRequest(BaseModel):
    subtask_id: int
    is_completed: int

@app.post("/api/toggle-subtask")
def toggle_subtask(payload: ToggleRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE subtasks SET is_completed = ? WHERE id = ?", (payload.is_completed, payload.subtask_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

# --- RENAMED ENDPOINT WITH ENRICHED STORAGE LOGIC ---
@app.post("/api/generate-plan")
def generate_plan(payload: TaskRequest):
    try:
        # Capture the current date for accurate deadline calculations
        current_time_string = datetime.now().strftime("%A, %B %d, %Y")

        prompt = f"""
        You are 'The Last-Minute Life Saver', an intelligent AI productivity coach.

        Current Date:
        {current_time_string}

        Use the current date above as the reference point when:
        - Calculating how much time remains until the deadline.
        - Determining the task priority (Low, Medium, High, or Critical).
        - Estimating the total hours of focused work required.

        User Task:
        {payload.task_title}

        Deadline:
        {payload.deadline}

        User Selected Difficulty:
        {payload.difficulty}

        Analyze the task and return:

        1. A priority level (Low, Medium, High, or Critical)
        2. A one-sentence reason explaining the priority
        3. Estimated active work hours required
        4. A list of 3–5 realistic, actionable subtasks that help complete the task before the deadline.

        Make the subtasks specific, practical, and ordered in the sequence they should be completed.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AISubtaskSchema,
                temperature=0.3,
            ),
        )

        validated_data = AISubtaskSchema.model_validate_json(response.text)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tasks
            (title, deadline, difficulty, priority, reason, estimated_hours)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.task_title,
                payload.deadline,
                payload.difficulty,
                validated_data.priority,
                validated_data.reason,
                validated_data.estimated_hours,
            ),
        )

        parent_task_id = cursor.lastrowid

        for subtask_title in validated_data.subtasks:
            cursor.execute(
                """
                INSERT INTO subtasks (task_id, title, is_completed)
                VALUES (?, ?, 0)
                """,
                (parent_task_id, subtask_title),
            )

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "task_id": parent_task_id,
            "priority": validated_data.priority,
            "reason": validated_data.reason,
            "estimated_hours": validated_data.estimated_hours,
            "subtasks": validated_data.subtasks,
        }

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        print(error_details)

        raise HTTPException(
            status_code=500,
            detail=f"Agent Error: {str(e)}"
        )