from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.rps import router as rps_router
from app.api.v1.quiz import router as quiz_router
from app.api.v1.grading import router as grading_router
from app.core.database import init_db

app = FastAPI(title="EduCopilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(rps_router, prefix="/api/rps", tags=["rps"])
app.include_router(quiz_router, prefix="/api/quiz", tags=["quiz"])
app.include_router(grading_router, prefix="/api/grading", tags=["grading"])

from app.api.v1.courses import router as courses_router
from app.api.v1.materials import router as materials_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.students import router as students_router
from app.api.v1.settings import router as settings_router

app.include_router(courses_router, prefix="/api/courses", tags=["courses"])
app.include_router(materials_router, prefix="/api/materials", tags=["materials"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(students_router, prefix="/api/students", tags=["students"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])


@app.on_event("startup")
def on_startup():
    init_db()