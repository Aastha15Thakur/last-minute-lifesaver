import os
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from typing import List,Literal
from database import get_db_connection
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:3000",
    "https://dash-frontend-526477031025.asia-south1.run.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
load_dotenv()
print("Loaded API Key:", os.getenv("GEMINI_API_KEY")[:10])
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

class CoachAnalysisResponse(BaseModel):
    status: Literal["On Track", "Slightly Behind", "High Risk"]
    risk_level: Literal["Low", "Medium", "High"]
    reason: str = Field(description="One concise sentence explaining the decision.")
    next_focus: str = Field(description="The single highest-impact remaining subtask the user should complete next.")


class RecoveryPlanResponse(BaseModel):
    summary: str = Field(description="A brief, motivational summary of the recovery strategy.")
    today: List[str] = Field(description="List of specific, actionable subtasks or study milestones to achieve today.")
    tomorrow: List[str] = Field(description="List of specific, actionable subtasks or study milestones to achieve tomorrow.")
    estimated_recovery: str = Field(description="A short phrase stating when they will be back on track (e.g., 'By tomorrow evening').")


@app.post("/api/toggle-subtask")
def toggle_subtask(payload: ToggleRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE subtasks SET is_completed = ? WHERE id = ?", (payload.is_completed, payload.subtask_id))
    conn.commit()
    conn.close()
    return {"status": "success"}


@app.post("/api/generate-plan")
def generate_plan(payload: TaskRequest):
    try:
        # Capture the current date for accurate deadline calculations
        current_time_string = datetime.now().strftime("%A,%B %d,%Y")

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
    

@app.get("/api/analyze-progress", response_model=CoachAnalysisResponse)
def analyze_progress():
    # 1. Open Database Connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 2. Fetch the latest task from the database
        cursor.execute("SELECT id, title, deadline, priority, estimated_hours, reason FROM tasks ORDER BY id DESC LIMIT 1")
        task_row = cursor.fetchone()
        
        if not task_row:
            raise HTTPException(status_code=404, detail="No tasks found to analyze.")
        
        task_id, task_title, deadline, priority, estimated_hours, reason = task_row
        
        # 3. Fetch all subtasks for this specific task
        cursor.execute("SELECT title, is_completed FROM subtasks WHERE task_id = ?", (task_id,))
        subtask_rows = cursor.fetchall()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close() # Always close the connection to prevent database locks
        
    # 4. Calculate metrics and sort titles
    total_subtasks = len(subtask_rows)
    completed_titles = []
    remaining_titles = []
    
    for row in subtask_rows:
        subtask_title, is_completed = row
        if is_completed == 1 or is_completed is True:
            completed_titles.append(subtask_title)
        else:
            remaining_titles.append(subtask_title)
            
    completed_count = len(completed_titles)
    remaining_count = len(remaining_titles)
    
    progress_percentage = 0.0
    if total_subtasks > 0:
        progress_percentage = round((completed_count / total_subtasks) * 100, 2)
        
    # 5. Build the context and call Gemini
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    You are an expert, empathetic, and highly strategic AI Productivity Coach for a student using "The Last-Minute Life Saver" app.
    Your job is to analyze their progress on a specific task, determine if they are on track, and tell them exactly what to look at next.

    Current Date (Today): {current_date}

    Task Details:
    - Task Name: {task_title}
    - Deadline: {deadline}
    - Priority: {priority}
    - Estimated Hours Required: {estimated_hours}
    - Original Intent/Reason: {reason}

    Subtask Metrics:
    - Total Subtasks: {total_subtasks}
    - Progress: {progress_percentage}% ({completed_count} completed, {remaining_count} remaining)

    Completed Subtasks:
    {", ".join(completed_titles) if completed_titles else "None yet"}

    Remaining Subtasks (Still Need Work):
    {", ".join(remaining_titles) if remaining_titles else "None! All done"}

    Analyze the remaining work against the deadline and today's date to determine status and risk. 
    Additionally, look closely at the "Remaining Subtasks" list and pick out the single most critical, highest-impact subtask they should tackle next to make meaningful progress.
    """

    try:
        # Reuses your existing 'client' instance from main.py
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CoachAnalysisResponse,
                temperature=0.2,
            ),
        )
        
        # Parse the structured response back to our Pydantic model
        return CoachAnalysisResponse.model_validate_json(response.text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Generation Error: {str(e)}")   

@app.get("/api/recovery-plan", response_model=RecoveryPlanResponse)
def get_recovery_plan():
    # 1. Open Database Connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 2. Fetch the latest task
        cursor.execute("SELECT id, title, deadline, priority, estimated_hours, reason FROM tasks ORDER BY id DESC LIMIT 1")
        task_row = cursor.fetchone()
        
        if not task_row:
            raise HTTPException(status_code=404, detail="No tasks found to generate a recovery plan.")
        
        task_id, task_title, deadline, priority, estimated_hours, reason = task_row
        
        # 3. Fetch all subtasks for this specific task
        cursor.execute("SELECT title, is_completed FROM subtasks WHERE task_id = ?", (task_id,))
        subtask_rows = cursor.fetchall()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close() # Always close the connection
        
    # 4. Filter for remaining subtasks
    completed_titles = []
    remaining_titles = []
    
    for row in subtask_rows:
        subtask_title, is_completed = row
        if is_completed == 1 or is_completed is True:
            completed_titles.append(subtask_title)
        else:
            remaining_titles.append(subtask_title)
            
    # 5. Build the context and call Gemini
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    You are an expert, highly encouraging AI Academic Recovery Planner for "The Last-Minute Life Saver" app.
    The student has fallen behind or needs a clear, tactical execution roadmap to beat their deadline.
    Your objective is to take their remaining subtasks and split them into a realistic, hyper-focused plan for Today and Tomorrow.

    Current Date (Today): {current_date}

    Task Context:
    - Task Name: {task_title}
    - Final Deadline: {deadline}
    - Priority: {priority}
    - Original Intent: {reason}

    Subtask Breakdown:
    - Already Completed: {", ".join(completed_titles) if completed_titles else "None yet"}
    - Remaining Subtasks (Must Be Scheduled): {", ".join(remaining_titles) if remaining_titles else "None! All done"}

    Instruction:
    1. Look at the remaining subtasks and distribute them strategically across 'today' and 'tomorrow'.
    2. Make sure the breakdown is realistic given the deadline.
    3. If all subtasks are already completed, return empty lists for today and tomorrow and write a celebratory summary.
    4.Unless there are no remaining tasks, provide 2–4 actionable items for both today and tomorrow whenever possible.
    """

    try:
        # Reuses your existing 'client' instance
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RecoveryPlanResponse,
                temperature=0.3,
            ),
        )
        
        print("Gemini Response:")
        print(response.text)
        return RecoveryPlanResponse.model_validate_json(response.text)
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )