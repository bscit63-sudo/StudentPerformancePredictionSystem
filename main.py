from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import ping_database
from app.routes import auth, teachers, students, weight_configs, performance_records, performance_scores, reports, attendance, courses, departments
@asynccontextmanager
async def lifespan(app: FastAPI):
    connected = await ping_database()
    print("Connected to MongoDB!" if connected else "FAILED to connect to MongoDB.")
    yield
app = FastAPI(lifespan=lifespan)

# Serve CSS/JS files from app/static at the URL path /static
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Set up Jinja2 to render HTML files from app/templates
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="admin_dashboard.html")

@app.get("/teacher/dashboard", response_class=HTMLResponse)
async def teacher_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="teacher_dashboard.html")

@app.get("/student/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="student_dashboard.html")

# Backend API routers
app.include_router(auth.router)
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(weight_configs.router)
app.include_router(performance_records.router)
app.include_router(performance_scores.router)
app.include_router(reports.router)
app.include_router(attendance.router)
app.include_router(courses.router)
app.include_router(departments.router)

@app.get("/health")
async def health_check():
    db_ok = await ping_database()
    return {"database_connected": db_ok}