from datetime import date, datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.healthcheck.router import router as healthcheck_router
from app.kafka import publish_event
from app.settings import settings

app = FastAPI(title="OMS5 Operations Service", version="0.1.0", root_path=settings.root_path)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8088", "http://127.0.0.1:8088"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(healthcheck_router)

clients: dict[str, dict] = {}
shifts: dict[str, dict] = {}
tasks: dict[str, dict] = {}
timesheets: dict[str, dict] = {}


class ClientCreate(BaseModel):
    name: str
    external_id: str | None = None


class ShiftCreate(BaseModel):
    client_id: str
    starts_at: datetime
    ends_at: datetime
    location: str | None = None


class TaskCreate(BaseModel):
    shift_id: str
    title: str
    description: str = ""
    assignee_employee_id: int | None = None


class TimesheetCreate(BaseModel):
    employee_id: int
    shift_id: str
    work_date: date
    hours: float = Field(gt=0, le=24)


@app.post("/clients")
def create_client(payload: ClientCreate) -> dict:
    item = {"id": str(uuid4()), **payload.model_dump(), "created_at": datetime.now(timezone.utc)}
    clients[item["id"]] = item
    publish_event("operations.client_created", item)
    return item


@app.post("/shifts")
def create_shift(payload: ShiftCreate) -> dict:
    if payload.client_id not in clients:
        raise HTTPException(status_code=404, detail="Client not found")
    item = {"id": str(uuid4()), **payload.model_dump(), "created_at": datetime.now(timezone.utc)}
    shifts[item["id"]] = item
    publish_event("operations.shift_created", item)
    return item


@app.post("/tasks")
def create_task(payload: TaskCreate) -> dict:
    if payload.shift_id not in shifts:
        raise HTTPException(status_code=404, detail="Shift not found")
    item = {"id": str(uuid4()), "status": "new", **payload.model_dump(), "created_at": datetime.now(timezone.utc)}
    tasks[item["id"]] = item
    publish_event("operations.task_created", item)
    return item


@app.post("/timesheets")
def create_timesheet(payload: TimesheetCreate) -> dict:
    if payload.shift_id not in shifts:
        raise HTTPException(status_code=404, detail="Shift not found")
    item = {"id": str(uuid4()), **payload.model_dump(), "created_at": datetime.now(timezone.utc)}
    timesheets[item["id"]] = item
    publish_event("operations.timesheet_created", item)
    return item


@app.get("/operations/summary")
def summary() -> dict:
    return {"clients": len(clients), "shifts": len(shifts), "tasks": len(tasks), "timesheets": len(timesheets)}
