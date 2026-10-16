
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.db.session import Base, engine
from app.models.user import User
from app.models.notification import Notification
from app.models.employee import Employee
from app.models.employee_document import EmployeeDocument
from app.models.leave import Leave
from app.models.payroll import Payroll
from app.routers.auth import (
    get_current_user,
    require_roles,
    router as auth_router,
)
from app.routers.employees import router as employees_router
from app.routers.employee_documents import router as employee_documents_router
from app.routers.attendance import router as attendance_router
from app.routers.leaves import router as leaves_router
from app.routers.payroll import router as payroll_router
from app.routers.reports import router as reports_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.holidays import router as holidays_router
from app.routers.working_days import router as working_days_router
from app.routers.shifts import router as shifts_router
from app.routers.notifications import router as notifications_router
from app.routers.notification_preferences import router as notification_preferences_router
from app.models.leave_balance import LeaveBalance
from app.models.leave_ledger import LeaveLedger
from app.models.audit_log import AuditLog
from app.models.holiday import Holiday

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Creates only missing tables; it does not reset existing tables or data.
from app.models.shift import Shift
from app.models.shift import EmployeeShift

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(employees_router)
app.include_router(employee_documents_router)
app.include_router(attendance_router)
app.include_router(leaves_router)
app.include_router(payroll_router)
app.include_router(reports_router)
app.include_router(audit_logs_router)
app.include_router(holidays_router)
app.include_router(working_days_router)
app.include_router(shifts_router)
app.include_router(notifications_router)
app.include_router(notification_preferences_router)


@app.get("/")
def home():
    return {"message": "HRMS API is running"}


@app.get("/health/db")
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"database": "connected"}


@app.get("/admin/test")
def admin_test(current_user=Depends(require_roles("admin"))):
    return {"message": "Admin access granted"}


@app.get("/hr/test")
def hr_test(current_user=Depends(require_roles("admin", "hr"))):
    return {"message": "HR access granted"}


@app.get("/employee/test")
def employee_test(current_user=Depends(get_current_user)):
    return {
        "message": "Authenticated access granted",
        "role": current_user.role,
    }

from app.routers import compensation
app.include_router(compensation.router)
