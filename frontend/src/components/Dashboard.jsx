import { useMemo, useState } from "react";
import {
  LayoutDashboard,
  Users,
  CalendarDays,
  ClipboardCheck,
  Wallet,
  FileDown,
  Search,
  Bell,
  LogOut,
  TrendingUp,
  CheckCircle2,
  Clock3,
  CircleDollarSign,
  ArrowUpRight,
  MoreHorizontal,
  RefreshCw,
  FileText,
  Building2,
  X,
} from "lucide-react";
import api from "../api/client";

const navigation = [
  { label: "Dashboard", icon: LayoutDashboard },
  { label: "Employees", icon: Users },
  { label: "Attendance", icon: CalendarDays },
  { label: "Leave Management", icon: ClipboardCheck },
  { label: "Payroll", icon: Wallet },
  { label: "Reports", icon: FileDown },
];

const demoLeaves = [
  {
    id: "LV001",
    name: "Rahul Raj",
    department: "Finance",
    type: "Sick Leave",
    dates: "20 Oct – 21 Oct",
    days: 2,
    status: "Pending",
    initials: "RR",
  },
  {
    id: "LV002",
    name: "Sneha Devi",
    department: "Design",
    type: "Casual Leave",
    dates: "22 Oct",
    days: 1,
    status: "Pending",
    initials: "SD",
  },
  {
    id: "LV003",
    name: "Arun Kumar",
    department: "Engineering",
    type: "Earned Leave",
    dates: "26 Oct – 28 Oct",
    days: 3,
    status: "Approved",
    initials: "AK",
  },
];

const demoAttendance = [
  { department: "Engineering", present: 42, total: 46, color: "blue" },
  { department: "Human Resources", present: 12, total: 14, color: "green" },
  { department: "Finance", present: 18, total: 20, color: "purple" },
  { department: "Design", present: 15, total: 16, color: "orange" },
];

const demoPayroll = [
  {
    id: "PAY001",
    name: "Arun Kumar",
    employeeId: "EMP001",
    period: "October 2026",
    basic: 25000,
    allowances: 3000,
    deductions: 1500,
    net: 26500,
  },
];

const formatCurrency = (amount) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);

function getEmployeeName(employee) {
  return (
    employee.name ||
    [employee.first_name, employee.last_name].filter(Boolean).join(" ") ||
    employee.full_name ||
    employee.email ||
    "Employee"
  );
}

function Avatar({ name, initials }) {
  const letters =
    initials ||
    name
      .split(/\s+/)
      .map((part) => part[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();

  return <div className="avatar">{letters}</div>;
}

function StatusBadge({ status }) {
  const normalized = String(status || "Active")
    .toLowerCase()
    .replace(/\s+/g, "-");

  return (
    <span className={`status-badge status-${normalized}`}>
      <span className="status-dot" />
      {status || "Active"}
    </span>
  );
}

function SectionHeading({ title, subtitle, action, onAction }) {
  return (
    <div className="section-heading">
      <div>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action && (
        <button className="text-action" onClick={onAction}>
          {action}
          <ArrowUpRight size={15} />
        </button>
      )}
    </div>
  );
}

function StatCard({ title, value, note, icon: Icon, variant }) {
  return (
    <article className="stat-card">
      <div className="stat-card-header">
        <span className="stat-label">{title}</span>
        <div className={`stat-icon stat-icon-${variant}`}>
          <Icon size={19} strokeWidth={1.8} />
        </div>
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-footer">
        <span className="stat-note">{note}</span>
      </div>
    </article>
  );
}

function EmployeeTable({ employees, onSelect }) {
  if (employees.length === 0) {
    return (
      <div className="dashboard-empty">
        No employee records found. Try another search or refresh the list.
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>EMPLOYEE</th>
            <th>DEPARTMENT</th>
            <th>DESIGNATION</th>
            <th>STATUS</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {employees.map((employee, index) => {
            const name = getEmployeeName(employee);
            return (
              <tr key={employee.id ?? employee.employee_id ?? index}>
                <td>
                  <div className="employee-identity">
                    <Avatar name={name} />
                    <div>
                      <strong>{name}</strong>
                      <span>
                        {employee.employee_code ||
                          employee.employee_id ||
                          (employee.id ? `EMP${employee.id}` : "Employee")}
                      </span>
                    </div>
                  </div>
                </td>
                <td>{employee.department || "—"}</td>
                <td>{employee.designation || employee.position || "—"}</td>
                <td>
                  <StatusBadge
                    status={
                      employee.status ||
                      (employee.is_active === false ? "Inactive" : "Active")
                    }
                  />
                </td>
                <td>
                  <button
                    className="row-action"
                    title={`View ${name}`}
                    aria-label={`View ${name}`}
                    onClick={() => onSelect(employee)}
                  >
                    <MoreHorizontal size={18} />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function Dashboard({ user, onLogout }) {
  const [activePage, setActivePage] = useState("Dashboard");
  const [showNotifications, setShowNotifications] = useState(false);
  const [search, setSearch] = useState("");
  const [employees, setEmployees] = useState([]);
  const [employeesLoaded, setEmployeesLoaded] = useState(false);
  const [employeesLoading, setEmployeesLoading] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [selectedEmployee, setSelectedEmployee] = useState(null);

  const [attendance, setAttendance] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [payroll, setPayroll] = useState([]);

  const [attendanceLoading, setAttendanceLoading] = useState(false);
  const [leavesLoading, setLeavesLoading] = useState(false);
  const [payrollLoading, setPayrollLoading] = useState(false);

  const [attendanceError, setAttendanceError] = useState("");
  const [attendanceActionLoading, setAttendanceActionLoading] = useState(false);
  const [attendanceActionMessage, setAttendanceActionMessage] = useState("");
  const [attendanceActionError, setAttendanceActionError] = useState("");
  const [leavesError, setLeavesError] = useState("");
  const [payrollError, setPayrollError] = useState("");

  const [attendanceLoaded, setAttendanceLoaded] = useState(false);
  const [leavesLoaded, setLeavesLoaded] = useState(false);
  const [payrollLoaded, setPayrollLoaded] = useState(false);

  const [showEmployeeForm, setShowEmployeeForm] = useState(false);
  const [employeeSaving, setEmployeeSaving] = useState(false);
  const [employeeFormError, setEmployeeFormError] = useState("");
  const [employeeForm, setEmployeeForm] = useState({
    full_name: "",
    employee_code: "",
    email: "",
    password: "",
    department: "",
    designation: "",
    joining_date: "",
    salary: "",
  });

  const displayName =
    user?.full_name ||
    user?.name ||
    user?.email ||
    user?.username ||
    "HRMS User";

  const filteredEmployees = useMemo(() => {
    const query = search.toLowerCase().trim();

    return employees.filter((employee) =>
      [
        getEmployeeName(employee),
        employee.id,
        employee.employee_code,
        employee.email,
        employee.department,
        employee.designation,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [employees, search]);


  const [leaveActionId, setLeaveActionId] = useState(null);
  const [leaveActionMessage, setLeaveActionMessage] = useState("");
  const [leaveActionError, setLeaveActionError] = useState("");
  const [leaveForm, setLeaveForm] = useState({
    start_date: "",
    end_date: "",
    leave_type: "casual",
    reason: "",
  });
  const [leaveSubmitting, setLeaveSubmitting] = useState(false);
  const [reportStartDate, setReportStartDate] = useState("");
  const [reportEndDate, setReportEndDate] = useState("");
  const [reportDepartment, setReportDepartment] = useState("");
  const [reportPayPeriod, setReportPayPeriod] = useState("");
  const [reportLoading, setReportLoading] = useState("");

  async function submitLeaveRequest(event) {
    event.preventDefault();
    setLeaveActionMessage("");
    setLeaveActionError("");

    if (!leaveForm.start_date || !leaveForm.end_date) {
      setLeaveActionError("Please select both leave dates.");
      return;
    }
    if (leaveForm.start_date < new Date().toLocaleDateString("en-CA")) {
      setLeaveActionError("Leave cannot start in the past.");
      return;
    }
    if (leaveForm.end_date < leaveForm.start_date) {
      setLeaveActionError("End date cannot be before the start date.");
      return;
    }
    if (leaveForm.reason.trim().length < 5) {
      setLeaveActionError("Please enter a reason of at least 5 characters.");
      return;
    }

    setLeaveSubmitting(true);
    try {
      await api.post("/leaves/", {
        start_date: leaveForm.start_date,
        end_date: leaveForm.end_date,
        leave_type: leaveForm.leave_type,
        reason: leaveForm.reason.trim(),
      });

      setLeaveActionMessage("Leave request submitted successfully.");
      setLeaveForm({
        start_date: "",
        end_date: "",
        leave_type: "casual",
        reason: "",
      });
      await loadLeaves();
    } catch (error) {
      const detail = error.response?.data?.detail;
      setLeaveActionError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((item) => item.msg).join(" | ")
            : "Unable to submit the leave request. Please try again."
      );
    } finally {
      setLeaveSubmitting(false);
    }
  }

  async function reviewLeave(leaveId, status) {
    const actionLabel = status === "approved" ? "approve" : "reject";
    if (!window.confirm(`Are you sure you want to ${actionLabel} leave request #${leaveId}?`)) {
      return;
    }

    setLeaveActionId(leaveId);
    setLeaveActionMessage("");
    setLeaveActionError("");

    try {
      await api.patch(`/leaves/${leaveId}/review`, { status });
      setLeaveActionMessage(`Leave request #${leaveId} ${status} successfully.`);
      await loadLeaves();
    } catch (error) {
      const detail = error.response?.data?.detail;
      setLeaveActionError(
        typeof detail === "string"
          ? detail
          : `Could not ${actionLabel} leave request. Please check your permissions and try again.`
      );
    } finally {
      setLeaveActionId(null);
    }
  }

  async function downloadReport(kind) {
    setReportLoading(kind);
    setLeaveActionError("");
    setLeaveActionMessage("");

    try {
      const params = {};
      if (reportDepartment.trim()) params.department = reportDepartment.trim();

      let endpoint;
      let filename;

      if (kind === "attendance") {
        endpoint = "/reports/attendance.csv";
        filename = "attendance-report.csv";
        if (reportStartDate) params.start_date = reportStartDate;
        if (reportEndDate) params.end_date = reportEndDate;
        if (reportStartDate && reportEndDate && reportEndDate < reportStartDate) {
          throw new Error("End date cannot be earlier than start date.");
        }
      } else {
        endpoint = "/reports/payroll.csv";
        filename = "payroll-report.csv";
        if (reportPayPeriod) params.pay_period = `${reportPayPeriod}-01`;
      }

      const response = await api.get(endpoint, {
        params,
        responseType: "blob",
      });

      const contentType = response.headers["content-type"] || "";
      if (!contentType.includes("text/csv") && !contentType.includes("application/octet-stream")) {
        const body = await response.data.text();
        throw new Error(body || "The server did not return a CSV file.");
      }

      const blob = new Blob([response.data], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);

      setLeaveActionMessage(
        `${kind === "attendance" ? "Attendance" : "Payroll"} CSV downloaded successfully.`
      );
    } catch (error) {
      let detail = error.response?.data?.detail;
      if (error.response?.data instanceof Blob) {
        try {
          const body = JSON.parse(await error.response.data.text());
          detail = body.detail;
        } catch {
          // Keep the fallback message below.
        }
      }
      setLeaveActionError(
        error.message || (typeof detail === "string" ? detail : "Report download failed.")
      );
    } finally {
      setReportLoading("");
    }
  }

  function renderReports() {
    return (
      <>
        <div className="page-intro">
          <div>
            <div className="eyebrow">DATA AND COMPLIANCE</div>
            <h1>Reports</h1>
            <p className="page-description">
              Export live attendance and payroll records as CSV files.
            </p>
          </div>
        </div>

        {leaveActionMessage && (
          <div className="report-feedback report-success" role="status">
            {leaveActionMessage}
          </div>
        )}
        {leaveActionError && (
          <div className="dashboard-error" role="alert">
            {leaveActionError}
          </div>
        )}

        <section className="panel page-panel report-panel">
          <SectionHeading
            title="Attendance report"
            subtitle="Optional date range and department filters"
          />
          <div className="report-filter-grid">
            <label>
              Start date
              <input type="date" value={reportStartDate}
                onChange={(event) => setReportStartDate(event.target.value)} />
            </label>
            <label>
              End date
              <input type="date" value={reportEndDate}
                onChange={(event) => setReportEndDate(event.target.value)} />
            </label>
            <label>
              Department
              <input type="text" value={reportDepartment}
                placeholder="All departments"
                onChange={(event) => setReportDepartment(event.target.value)} />
            </label>
          </div>
          <button className="button button-primary"
            disabled={Boolean(reportLoading)}
            onClick={() => downloadReport("attendance")}>
            <FileDown size={16} />
            {reportLoading === "attendance" ? "Downloading..." : "Download attendance CSV"}
          </button>
        </section>

        <section className="panel page-panel report-panel">
          <SectionHeading
            title="Payroll report"
            subtitle="Optional pay period and department filters"
          />
          <div className="report-filter-grid">
            <label>
              Pay period
              <input type="month" value={reportPayPeriod}
                onChange={(event) => setReportPayPeriod(event.target.value)} />
            </label>
            <label>
              Department
              <input type="text" value={reportDepartment}
                placeholder="All departments"
                onChange={(event) => setReportDepartment(event.target.value)} />
            </label>
          </div>
          <button className="button button-primary"
            disabled={Boolean(reportLoading)}
            onClick={() => downloadReport("payroll")}>
            <FileDown size={16} />
            {reportLoading === "payroll" ? "Downloading..." : "Download payroll CSV"}
          </button>
        </section>
      </>
    );
  }

  async function loadEmployees() {
    setActivePage("Employees");
    setLoadError("");
    setEmployeesLoading(true);

    try {
      const response = await api.get("/employees/");
      const data = response.data;

      const records = Array.isArray(data)
        ? data
        : Array.isArray(data?.items)
          ? data.items
          : Array.isArray(data?.employees)
            ? data.employees
            : [];

      setEmployees(records);
      setEmployeesLoaded(true);
    } catch (error) {
      setLoadError(
        typeof error.response?.data?.detail === "string"
          ? error.response.data.detail
          : "Unable to load employee records. Check the API response and account permissions."
      );
    } finally {
      setEmployeesLoading(false);
    }
  }


  
  async function handleCreateEmployee(event) {
    event.preventDefault();
    setEmployeeSaving(true);
    setEmployeeFormError("");

    try {
      await api.post("/employees/", employeeForm);

      setEmployeeForm({
        full_name: "",
        employee_code: "",
        email: "",
        password: "",
        department: "",
        designation: "",
        joining_date: "",
        salary: "",
      });

      setShowEmployeeForm(false);
      await loadEmployees();
    } catch (error) {
      const detail = error.response?.data?.detail;

      setEmployeeFormError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((item) => `${item.loc?.slice(-1)[0]}: ${item.msg}`).join(" | ")
            : JSON.stringify(detail || error.message)
      );
    } finally {
      setEmployeeSaving(false);
    }
  }


  async function handleEmployeeCheckIn() {
    setAttendanceActionLoading(true);
    setAttendanceActionMessage("");
    setAttendanceActionError("");
    try {
      const today = new Date().toLocaleDateString("en-CA");
      await api.post("/attendance/check-in", { attendance_date: today });
      setAttendanceActionMessage("Check-in recorded successfully.");
      await loadAttendance();
    } catch (error) {
      const detail = error.response?.data?.detail;
      setAttendanceActionError(
        typeof detail === "string" ? detail : "Unable to check in. Please try again."
      );
      await loadAttendance();
    } finally {
      setAttendanceActionLoading(false);
    }
  }

  async function handleEmployeeCheckOut(attendanceId) {
    setAttendanceActionLoading(true);
    setAttendanceActionMessage("");
    setAttendanceActionError("");
    try {
      await api.patch(`/attendance/${attendanceId}/check-out`);
      setAttendanceActionMessage("Check-out recorded successfully.");
      await loadAttendance();
    } catch (error) {
      const detail = error.response?.data?.detail;
      setAttendanceActionError(
        typeof detail === "string" ? detail : "Unable to check out. Please try again."
      );
      await loadAttendance();
    } finally {
      setAttendanceActionLoading(false);
    }
  }

  async function loadAttendance() {
    setAttendanceLoading(true);
    setAttendanceError("");
    try {
      const response = await api.get("/attendance/");
      setAttendance(Array.isArray(response.data) ? response.data : []);
      setAttendanceLoaded(true);
    } catch (error) {
      setAttendanceError(
        typeof error.response?.data?.detail === "string"
          ? error.response.data.detail
          : "Unable to load attendance records."
      );
    } finally {
      setAttendanceLoading(false);
    }
  }

  async function loadLeaves() {
    setLeavesLoading(true);
    setLeavesError("");
    try {
      const response = await api.get("/leaves/");
      setLeaves(Array.isArray(response.data) ? response.data : []);
      setLeavesLoaded(true);
    } catch (error) {
      setLeavesError(
        typeof error.response?.data?.detail === "string"
          ? error.response.data.detail
          : "Unable to load leave requests."
      );
    } finally {
      setLeavesLoading(false);
    }
  }

  async function loadPayroll() {
    setPayrollLoading(true);
    setPayrollError("");
    try {
      const response = await api.get("/payroll/");
      setPayroll(Array.isArray(response.data) ? response.data : []);
      setPayrollLoaded(true);
    } catch (error) {
      setPayrollError(
        typeof error.response?.data?.detail === "string"
          ? error.response.data.detail
          : "Unable to load payroll records."
      );
    } finally {
      setPayrollLoading(false);
    }
  }

  
  function openPage(page) {
    setActivePage(page);
    setSearch("");
    setSelectedEmployee(null);

    const role = String(user?.role || "").toLowerCase();
    const isEmployee = role === "employee";
    const isAdminOrHR = role === "admin" || role === "hr";

    if (page === "Employees") {
      if (isAdminOrHR && !employeesLoaded) loadEmployees();
      return;
    }

    if (page === "Attendance") {
      if (!attendanceLoaded) loadAttendance();
      return;
    }

    if (page === "Leave Management") {
      if (!leavesLoaded) loadLeaves();
      return;
    }

    if (page === "Payroll") {
      if (!isEmployee && !payrollLoaded) loadPayroll();
      return;
    }
  }

  function renderDashboard() {
    const today = new Date().toLocaleDateString("en-CA");
    const currentMonth = today.slice(0, 7);

    const todayAttendance = attendance.filter(
      (record) =>
        String(record.attendance_date).slice(0, 10) === today
    );

    const presentCount = todayAttendance.filter(
      (record) => record.status?.toLowerCase() === "present"
    ).length;

    const pendingLeaves = leaves.filter(
      (leave) => leave.status?.toLowerCase() === "pending"
    );

    const currentMonthPayroll = payroll.filter(
      (record) =>
        String(record.pay_period).slice(0, 7) === currentMonth
    );

    const monthlyPayrollTotal = currentMonthPayroll.reduce(
      (total, record) => total + Number(record.net_salary || 0),
      0
    );

    const formatDate = (value) => {
      if (!value) return "—";

      const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);

      return Number.isNaN(date.getTime())
        ? String(value)
        : date.toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
          });
    };

    const formatPeriod = (value) => {
      if (!value) return "—";

      const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);

      return Number.isNaN(date.getTime())
        ? String(value)
        : date.toLocaleDateString("en-IN", {
            month: "long",
            year: "numeric",
          });
    };

    const employeeFor = (employeeId) =>
      employees.find((employee) => employee.id === employeeId);

    const employeeNameFor = (employeeId) => {
      const employee = employeeFor(employeeId);
      return employee
        ? getEmployeeName(employee)
        : `Employee #${employeeId}`;
    };

    const leaveDays = (leave) => {
      if (!leave.start_date || !leave.end_date) return 0;

      const start = new Date(
        `${String(leave.start_date).slice(0, 10)}T00:00:00`
      );
      const end = new Date(
        `${String(leave.end_date).slice(0, 10)}T00:00:00`
      );

      if (
        Number.isNaN(start.getTime()) ||
        Number.isNaN(end.getTime()) ||
        end < start
      ) {
        return 0;
      }

      return Math.round((end - start) / 86400000) + 1;
    };

    const recentLeaves = [...leaves]
      .sort(
        (a, b) =>
          new Date(b.created_at || b.start_date || 0) -
          new Date(a.created_at || a.start_date || 0)
      )
      .slice(0, 3);

    const recentPayroll = [...currentMonthPayroll].slice(0, 5);

    return (
      <>
        
        <div className="page-intro">
          <div>
            <div className="eyebrow">PEOPLE OPERATIONS</div>
            <h1>Dashboard</h1>
            <p className="page-description">
              Here is your workforce overview and HR activity.
            </p>
          </div>

          <div className="employee-header-actions">
            <button
              className="button button-secondary"
              onClick={loadEmployees}
              disabled={employeesLoading}
            >
              <RefreshCw size={15} />
              Refresh records
            </button>

            <button
              className="button button-primary"
              onClick={() => {
                setActivePage("Employees");
                setSearch("");
                setEmployeeFormError("");
                setShowEmployeeForm(true);
                if (!employeesLoaded) loadEmployees();
              }}
            >
              + Add Employee
            </button>
          </div>
        </div>


        <div className="demo-banner">
          <FileText size={16} />
          <span>
            <strong>Data status:</strong>{" "}
            Employees: {employeesLoaded ? "loaded" : "not loaded"};{" "}
            Attendance: {attendanceLoaded ? "loaded" : "not loaded"};{" "}
            Leave: {leavesLoaded ? "loaded" : "not loaded"};{" "}
            Payroll: {payrollLoaded ? "loaded" : "not loaded"}.
          </span>
        </div>

        <section className="stats-grid">
          <StatCard
            title="Total employees"
            value={employeesLoaded ? String(employees.length) : "—"}
            note={employeesLoaded ? "Records returned by API" : "Employee data not loaded"}
            icon={Users}
            variant="blue"
          />
          <StatCard
            title="Present today"
            value={attendanceLoaded ? String(presentCount) : "—"}
            note="Today's recorded present employees"
            icon={CheckCircle2}
            variant="green"
          />
          <StatCard
            title="Pending leave requests"
            value={leavesLoaded ? String(pendingLeaves.length).padStart(2, "0") : "—"}
            note="Requests awaiting review"
            icon={Clock3}
            variant="orange"
          />
          <StatCard
            title="Monthly payroll"
            value={payrollLoaded ? formatCurrency(monthlyPayrollTotal) : "—"}
            note="Current month net salaries"
            icon={CircleDollarSign}
            variant="purple"
          />
        </section>

        <section className="dashboard-grid">
          <article className="panel employee-panel">
            <SectionHeading
              title="Employee directory"
              subtitle={
                employeesLoaded
                  ? `${employees.length} records loaded from the API`
                  : "Load your current employee records"
              }
              action="View all"
              onAction={() => openPage("Employees")}
            />

            {employeesLoading ? (
              <div className="dashboard-empty">Loading employees...</div>
            ) : loadError && !employeesLoaded ? (
              <div className="dashboard-error">{loadError}</div>
            ) : employeesLoaded ? (
              <EmployeeTable
                employees={employees.slice(0, 5)}
                onSelect={setSelectedEmployee}
              />
            ) : (
              <div className="dashboard-empty">
                <Users size={24} />
                <strong>Employee records</strong>
                <span>
                  Load the employee API to display your current workforce.
                </span>
                <button
                  className="button button-primary"
                  onClick={loadEmployees}
                >
                  Load employees
                </button>
              </div>
            )}

            {selectedEmployee && (
              <div className="selected-employee">
                <div>
                  <strong>{getEmployeeName(selectedEmployee)}</strong>
                  <span>
                    {selectedEmployee.email || "No email available"}
                    {" · "}
                    {selectedEmployee.department || "No department"}
                  </span>
                </div>
                <button
                  className="icon-button"
                  aria-label="Close employee details"
                  onClick={() => setSelectedEmployee(null)}
                >
                  <X size={16} />
                </button>
              </div>
            )}
          </article>

          <article className="panel requests-panel">
            <SectionHeading
              title="Recent leave requests"
              subtitle={
                leavesLoaded
                  ? `${leaves.length} live request(s)`
                  : "Leave data not loaded"
              }
              action="View all"
              onAction={() => openPage("Leave Management")}
            />

            {!leavesLoaded ? (
              <div className="dashboard-empty">Leave records have not loaded.</div>
            ) : recentLeaves.length === 0 ? (
              <div className="dashboard-empty">No leave requests found.</div>
            ) : (
              <div className="leave-list">
                {recentLeaves.map((leave) => {
                  const name = employeeNameFor(leave.employee_id);
                  const type = leave.leave_type
                    ? leave.leave_type.replaceAll("_", " ")
                    : "Leave";

                  return (
                    <div className="leave-item" key={leave.id}>
                      <Avatar name={name} />
                      <div className="leave-person">
                        <strong>{name}</strong>
                        <span>{type}</span>
                        <small>
                          {formatDate(leave.start_date)} –{" "}
                          {formatDate(leave.end_date)}
                        </small>
                      </div>
                      <StatusBadge status={leave.status || "pending"} />
                    </div>
                  );
                })}
              </div>
            )}

            <button
              className="button button-secondary button-full"
              onClick={() => openPage("Leave Management")}
            >
              Review leave requests
              <ArrowUpRight size={15} />
            </button>
          </article>
        </section>

        <section className="bottom-grid">
          <article className="panel attendance-panel">
            <SectionHeading
              title="Attendance overview"
              subtitle="Today's actual attendance records"
              action="View details"
              onAction={() => openPage("Attendance")}
            />

            <div className="attendance-total">
              <div>
                <strong>
                  {attendanceLoaded && employeesLoaded && employees.length > 0
                    ? `${Math.round((presentCount / employees.length) * 100)}%`
                    : "—"}
                </strong>
                <span>Present / total employees</span>
              </div>
              <span className="attendance-count">
                {attendanceLoaded
                  ? `${presentCount} present today`
                  : "Attendance data not loaded"}
              </span>
            </div>

            {!attendanceLoaded ? (
              <div className="dashboard-empty">
                Attendance records have not loaded.
              </div>
            ) : todayAttendance.length === 0 ? (
              <div className="dashboard-empty">
                No attendance records for today.
              </div>
            ) : (
              <div className="department-list">
                {todayAttendance.slice(0, 5).map((record) => (
                  <div className="department-row" key={record.id}>
                    <div className="department-label">
                      <span>{employeeNameFor(record.employee_id)}</span>
                      <strong>
                        {(record.status || "unknown").replaceAll("_", " ")}
                      </strong>
                    </div>
                    <div className="progress-track">
                      <div
                        className={`progress-fill ${
                          record.status?.toLowerCase() === "present"
                            ? "fill-green"
                            : "fill-blue"
                        }`}
                        style={{
                          width:
                            record.status?.toLowerCase() === "present"
                              ? "100%"
                              : "0%",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="panel payroll-panel">
            <SectionHeading
              title="Payroll summary"
              subtitle="Actual salary records"
              action="View payroll"
              onAction={() => openPage("Payroll")}
            />

            <div className="payroll-period">
              <span>Payroll period</span>
              <strong>{formatPeriod(`${currentMonth}-01`)}</strong>
            </div>

            <div className="payroll-amount">
              {payrollLoaded ? formatCurrency(monthlyPayrollTotal) : "—"}
            </div>
            <div className="payroll-caption">
              Current month net payroll
            </div>

            <div className="payroll-breakdown">
              <div>
                <span>Payroll records</span>
                <strong>
                  {payrollLoaded ? currentMonthPayroll.length : "—"}
                </strong>
              </div>
              <div>
                <span>Pending processing</span>
                <strong>—</strong>
              </div>
            </div>

            {payrollLoaded && recentPayroll.length > 0 && (
              <div className="payroll-note">
                <TrendingUp size={15} />
                <span>
                  Latest record: {employeeNameFor(recentPayroll[0].employee_id)}{" "}
                  · {formatCurrency(Number(recentPayroll[0].net_salary || 0))}
                </span>
              </div>
            )}
          </article>
        </section>
      </>
    );
  }


  
  function renderEmployees() {
    const updateEmployeeField = (field, value) => {
      setEmployeeForm((previous) => ({
        ...previous,
        [field]: value,
      }));
    };

    return (
      <>
        <div className="page-intro">
          <div>
            <div className="eyebrow">PEOPLE OPERATIONS</div>
            <h1>Employees</h1>
            <p className="page-description">
              Browse and manage employee information from your backend.
            </p>
          </div>

          <div className="employee-header-actions">
            <button
              className="button button-secondary"
              onClick={loadEmployees}
              disabled={employeesLoading}
            >
              <RefreshCw size={15} />
              Refresh records
            </button>

            <button
              className="button button-primary"
              onClick={() => {
                setEmployeeFormError("");
                setShowEmployeeForm((current) => !current);
              }}
            >
              {showEmployeeForm ? "Cancel" : "+ Add Employee"}
            </button>
          </div>
        </div>

        {showEmployeeForm && (
          <section className="panel page-panel">
            <SectionHeading
              title="Add employee"
              subtitle="Enter the employee details below."
            />

            {employeeFormError && (
              <div className="dashboard-error">{employeeFormError}</div>
            )}

            <form
              className="employee-form"
              onSubmit={handleCreateEmployee}
            >
              
              <label>
                Full name
                <input
                  required
                  value={employeeForm.full_name}
                  onChange={(event) =>
                    setEmployeeForm((prev) => ({ ...prev, full_name: event.target.value }))
                  }
                  placeholder="Enter full name"
                />
              </label>

              <label>
                Employee code
                <input
                  required
                  value={employeeForm.employee_code}
                  onChange={(event) =>
                    setEmployeeForm((prev) => ({ ...prev, employee_code: event.target.value }))
                  }
                  placeholder="e.g. EMP003"
                />
              </label>

              <label>
                Email
                <input
                  required
                  type="email"
                  value={employeeForm.email}
                  onChange={(event) =>
                    setEmployeeForm((prev) => ({ ...prev, email: event.target.value }))
                  }
                  placeholder="employee@example.com"
                />
              </label>

              <label>
                Temporary password
                <input
                  required
                  type="password"
                  minLength={8}
                  value={employeeForm.password}
                  onChange={(event) =>
                    setEmployeeForm((prev) => ({ ...prev, password: event.target.value }))
                  }
                  placeholder="At least 8 characters"
                />
              </label>

              <label>
                Department
                <input
                  required
                  value={employeeForm.department}
                  onChange={(event) =>
                    setEmployeeForm((prev) => ({ ...prev, department: event.target.value }))
                  }
                  placeholder="e.g. Engineering"
                />
              </label>

              <label>
                Designation
                <input
                  required
                  value={employeeForm.designation}
                  onChange={(event) =>
                    setEmployeeForm((prev) => ({ ...prev, designation: event.target.value }))
                  }
                  placeholder="e.g. Software Developer"
                />
              </label>

              <label>
                Joining date
                <input
                  type="date"
                  required
                  value={employeeForm.joining_date}
                  onChange={(event) =>
                    setEmployeeForm((prev) => ({
                      ...prev,
                      joining_date: event.target.value,
                    }))
                  }
                />
              </label>

              <label>
                Salary (₹)
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  required
                  value={employeeForm.salary}
                  onChange={(event) =>
                    setEmployeeForm((prev) => ({
                      ...prev,
                      salary: event.target.value,
                    }))
                  }
                  placeholder="e.g. 25000"
                />
              </label>


              <div className="employee-form-actions">
                <button
                  type="submit"
                  className="button button-primary"
                  disabled={employeeSaving}
                >
                  {employeeSaving ? "Saving..." : "Create employee"}
                </button>

                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => setShowEmployeeForm(false)}
                  disabled={employeeSaving}
                >
                  Cancel
                </button>
              </div>
            </form>
          </section>
        )}

        <section className="panel page-panel">
          <SectionHeading
            title="Employee directory"
            subtitle={
              employeesLoaded
                ? `${filteredEmployees.length} of ${employees.length} records`
                : "Employee records from the API"
            }
          />

          {loadError && (
            <div className="dashboard-error">{loadError}</div>
          )}

          {employeesLoading ? (
            <div className="dashboard-empty">Loading employee records...</div>
          ) : employeesLoaded ? (
            <EmployeeTable
              employees={filteredEmployees}
              onSelect={setSelectedEmployee}
            />
          ) : (
            <div className="dashboard-empty">
              <Users size={24} />
              <strong>Employee records not loaded</strong>
              <span>Load records from your FastAPI backend.</span>
              <button
                className="button button-primary"
                onClick={loadEmployees}
              >
                Load employees
              </button>
            </div>
          )}

          {selectedEmployee && (
            <div className="selected-employee">
              <div>
                <strong>{getEmployeeName(selectedEmployee)}</strong>
                <span>
                  {selectedEmployee.email || "No email available"}
                  {" · "}
                  {selectedEmployee.designation || "No designation"}
                  {" · "}
                  {selectedEmployee.department || "No department"}
                </span>
              </div>

              <button
                className="icon-button"
                aria-label="Close employee details"
                onClick={() => setSelectedEmployee(null)}
              >
                <X size={16} />
              </button>
            </div>
          )}
        </section>
      </>
    );
  }



  function renderAttendance() {
    const today = new Date().toLocaleDateString("en-CA");
    const todayRecords = attendance.filter(
      (record) => String(record.attendance_date).slice(0, 10) === today
    );

    const presentCount = todayRecords.filter(
      (record) => record.status?.toLowerCase() === "present"
    ).length;

    const lateCount = todayRecords.filter(
      (record) => record.status?.toLowerCase() === "late"
    ).length;

    const absentCount = todayRecords.filter(
      (record) => record.status?.toLowerCase() === "absent"
    ).length;

    const attendanceRate =
      employeesLoaded && employees.length > 0
        ? Math.round((presentCount / employees.length) * 100)
        : null;

    return (
      <>
        <div className="page-intro">
          <div>
            <div className="eyebrow">WORKFORCE OPERATIONS</div>
            <h1>Attendance</h1>
            <p className="page-description">
              Live attendance records from your HRMS database.
            </p>
          </div>
        </div>

        {user?.role === "employee" && (
          <section className="panel page-panel employee-attendance-panel">
            <div className="employee-attendance-heading">
              <div>
                <h2>My attendance today</h2>
                <p>Record your working hours for today.</p>
              </div>
              <span className={
                todayRecords.length === 0
                  ? "employee-attendance-status status-not-started"
                  : todayRecords[0]?.check_out
                    ? "employee-attendance-status status-complete"
                    : "employee-attendance-status status-active"
              }>
                {todayRecords.length === 0
                  ? "Not checked in"
                  : todayRecords[0]?.check_out
                    ? "Shift completed"
                    : "Shift in progress"}
              </span>
            </div>

            {attendanceActionMessage && (
              <div className="report-feedback report-success" role="status">
                {attendanceActionMessage}
              </div>
            )}
            {attendanceActionError && (
              <div className="report-feedback report-error" role="alert">
                {attendanceActionError}
              </div>
            )}

            <div className="employee-attendance-times">
              <div>
                <span>Check-in time</span>
                <strong>
                  {todayRecords[0]?.check_in
                    ? new Date(todayRecords[0].check_in).toLocaleTimeString([], {
                        hour: "2-digit", minute: "2-digit"
                      })
                    : "—"}
                </strong>
              </div>
              <div>
                <span>Check-out time</span>
                <strong>
                  {todayRecords[0]?.check_out
                    ? new Date(todayRecords[0].check_out).toLocaleTimeString([], {
                        hour: "2-digit", minute: "2-digit"
                      })
                    : "—"}
                </strong>
              </div>
            </div>

            <div className="employee-attendance-actions">
              {todayRecords.length === 0 ? (
                <button
                  type="button"
                  className="button button-primary"
                  onClick={handleEmployeeCheckIn}
                  disabled={attendanceActionLoading || attendanceLoading}
                >
                  {attendanceActionLoading ? "Processing..." : "Check In"}
                </button>
              ) : !todayRecords[0]?.check_out ? (
                <button
                  type="button"
                  className="button button-primary"
                  onClick={() => handleEmployeeCheckOut(todayRecords[0].id)}
                  disabled={attendanceActionLoading || attendanceLoading}
                >
                  {attendanceActionLoading ? "Processing..." : "Check Out"}
                </button>
              ) : (
                <p className="employee-attendance-complete">
                  Your attendance for today is complete.
                </p>
              )}
            </div>
          </section>
        )}

        {attendanceLoading && (
          <div className="demo-banner">
            <FileText size={16} />
            <span>Loading attendance records...</span>
          </div>
        )}

        {attendanceError && (
          <div className="dashboard-error">
            {attendanceError}
            <button onClick={loadAttendance}>Retry</button>
          </div>
        )}

        {!attendanceLoading && !attendanceError && (
          <>
            <section className="stats-grid">
              <StatCard
                title="Present today"
                value={attendanceLoaded ? String(presentCount) : "—"}
                note="Actual attendance records"
                icon={CheckCircle2}
                variant="green"
              />
              <StatCard
                title="Late today"
                value={attendanceLoaded ? String(lateCount) : "—"}
                note="Marked late"
                icon={CalendarDays}
                variant="orange"
              />
              <StatCard
                title="Absent records"
                value={attendanceLoaded ? String(absentCount) : "—"}
                note="Explicitly marked absent"
                icon={Clock3}
                variant="blue"
              />
              <StatCard
                title="Attendance rate"
                value={
                  attendanceLoaded && attendanceRate !== null
                    ? `${attendanceRate}%`
                    : "—"
                }
                note={
                  employeesLoaded
                    ? "Present today / total employees"
                    : "Employee data required"
                }
                icon={TrendingUp}
                variant="purple"
              />
            </section>

            <section className="panel page-panel">
              <SectionHeading
                title="Today's attendance"
                subtitle={`${todayRecords.length} attendance record(s) for ${today}`}
              />

              {todayRecords.length === 0 ? (
                <div className="dashboard-empty">
                  No attendance records found for today.
                </div>
              ) : (
                <div className="table-scroll">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Check-in</th>
                        <th>Check-out</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {todayRecords.map((record) => {
                        const employee = employees.find(
                          (item) => item.id === record.employee_id
                        );

                        const employeeName = employee
                          ? getEmployeeName(employee)
                          : `Employee #${record.employee_id}`;

                        const formatTime = (value) =>
                          value
                            ? new Date(value).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : "—";

                        return (
                          <tr key={record.id}>
                            <td>
                              <strong>{employeeName}</strong>
                            </td>
                            <td>{formatTime(record.check_in)}</td>
                            <td>{formatTime(record.check_out)}</td>
                            <td>
                              <StatusBadge
                                status={record.status || "unknown"}
                              />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </>
    );
  }



  function renderLeaveManagement() {
    const getLeaveDays = (leave) => {
      if (!leave.start_date || !leave.end_date) return 0;

      const start = new Date(`${String(leave.start_date).slice(0, 10)}T00:00:00`);
      const end = new Date(`${String(leave.end_date).slice(0, 10)}T00:00:00`);

      if (
        Number.isNaN(start.getTime()) ||
        Number.isNaN(end.getTime()) ||
        end < start
      ) {
        return 0;
      }

      return Math.round((end - start) / 86400000) + 1;
    };

    const pendingCount = leaves.filter(
      (leave) => leave.status?.toLowerCase() === "pending"
    ).length;

    const approvedCount = leaves.filter(
      (leave) => leave.status?.toLowerCase() === "approved"
    ).length;

    const requestedDays = leaves.reduce(
      (total, leave) => total + getLeaveDays(leave),
      0
    );

    const categoriesCount = new Set(
      leaves.map((leave) => leave.leave_type).filter(Boolean)
    ).size;

    const formatDate = (value) => {
      if (!value) return "—";

      const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);

      return Number.isNaN(date.getTime())
        ? String(value)
        : date.toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          });
    };

    const formatLeaveType = (value) =>
      value
        ? value
            .replaceAll("_", " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase())
        : "—";

    const getEmployeeForLeave = (leave) =>
      employees.find((employee) => employee.id === leave.employee_id);

    return (
      <>
        <div className="page-intro">
          <div>
            <div className="eyebrow">PEOPLE OPERATIONS</div>
            <h1>Leave management</h1>
            <p className="page-description">
              Review leave requests and their current statuses.
            </p>
          </div>
        </div>

        {leaveActionMessage && (
          <div className="report-feedback report-success" role="status">
            {leaveActionMessage}
          </div>
        )}
        {leaveActionError && (
          <div className="dashboard-error" role="alert">
            {leaveActionError}
          </div>
        )}

        {user?.role === "employee" && (
          <section className="panel page-panel">
            <SectionHeading
              title="Apply for leave"
              subtitle="Submit a request for Admin/HR review"
            />
            <form className="employee-form" onSubmit={submitLeaveRequest}>
              <div className="report-filter-grid">
                <label>
                  Leave type
                  <select
                    value={leaveForm.leave_type}
                    onChange={(event) =>
                      setLeaveForm((current) => ({
                        ...current,
                        leave_type: event.target.value,
                      }))
                    }
                    required
                  >
                    <option value="casual">Casual Leave</option>
                    <option value="sick">Sick Leave</option>
                    <option value="earned">Earned Leave</option>
                    <option value="unpaid">Unpaid Leave</option>
                  </select>
                </label>
                <label>
                  Start date
                  <input
                    type="date"
                    value={leaveForm.start_date}
                    min={new Date().toLocaleDateString("en-CA")}
                    onChange={(event) =>
                      setLeaveForm((current) => ({
                        ...current,
                        start_date: event.target.value,
                        end_date:
                          current.end_date && current.end_date < event.target.value
                            ? event.target.value
                            : current.end_date,
                      }))
                    }
                    required
                  />
                </label>
                <label>
                  End date
                  <input
                    type="date"
                    value={leaveForm.end_date}
                    min={leaveForm.start_date || new Date().toLocaleDateString("en-CA")}
                    onChange={(event) =>
                      setLeaveForm((current) => ({
                        ...current,
                        end_date: event.target.value,
                      }))
                    }
                    required
                  />
                </label>
              </div>
              <label>
                Reason for leave
                <textarea
                  value={leaveForm.reason}
                  onChange={(event) =>
                    setLeaveForm((current) => ({
                      ...current,
                      reason: event.target.value,
                    }))
                  }
                  minLength={5}
                  maxLength={1000}
                  rows={4}
                  placeholder="Explain why you need leave (5–1000 characters)"
                  required
                />
              </label>
              <button
                type="submit"
                className="button button-primary"
                disabled={leaveSubmitting}
              >
                {leaveSubmitting ? "Submitting..." : "Submit leave request"}
              </button>
            </form>
          </section>
        )}

        {leavesLoading && (
          <div className="demo-banner">
            <FileText size={16} />
            <span>Loading leave requests...</span>
          </div>
        )}

        {leavesError && (
          <div className="dashboard-error">
            {leavesError}
            <button onClick={loadLeaves}>Retry</button>
          </div>
        )}

        {!leavesLoading && !leavesError && (
          <>
            <section className="stats-grid">
              <StatCard
                title="Pending requests"
                value={leavesLoaded ? String(pendingCount).padStart(2, "0") : "—"}
                note="Live database records"
                icon={Clock3}
                variant="orange"
              />
              <StatCard
                title="Approved requests"
                value={leavesLoaded ? String(approvedCount).padStart(2, "0") : "—"}
                note="Live database records"
                icon={CheckCircle2}
                variant="green"
              />
              <StatCard
                title="Requested leave days"
                value={leavesLoaded ? String(requestedDays).padStart(2, "0") : "—"}
                note="Inclusive calendar days"
                icon={CalendarDays}
                variant="blue"
              />
              <StatCard
                title="Leave categories"
                value={leavesLoaded ? String(categoriesCount).padStart(2, "0") : "—"}
                note="Distinct leave types"
                icon={ClipboardCheck}
                variant="purple"
              />
            </section>

            <section className="panel page-panel">
              <SectionHeading
                title="Leave applications"
                subtitle={`${leaves.length} live request(s)`}
              />

              {leaves.length === 0 ? (
                <div className="dashboard-empty">
                  No leave requests found.
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>EMPLOYEE</th>
                        <th>DEPARTMENT</th>
                        <th>LEAVE TYPE</th>
                        <th>DATES</th>
                        <th>DAYS</th>
                        <th>STATUS</th>
                        <th>ACTIONS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {leaves.map((leave) => {
                        const employee = getEmployeeForLeave(leave);
                        const employeeName = employee
                          ? getEmployeeName(employee)
                          : `Employee #${leave.employee_id}`;

                        const initials = employeeName
                          .split(" ")
                          .filter(Boolean)
                          .map((part) => part[0])
                          .join("")
                          .slice(0, 2)
                          .toUpperCase();

                        return (
                          <tr key={leave.id}>
                            <td>
                              <div className="employee-identity">
                                <Avatar
                                  name={employeeName}
                                  initials={initials}
                                />
                                <div>
                                  <strong>{employeeName}</strong>
                                  <span>#{leave.employee_id}</span>
                                </div>
                              </div>
                            </td>
                            <td>
                              {employee?.department || employee?.department_name || "—"}
                            </td>
                            <td>{formatLeaveType(leave.leave_type)}</td>
                            <td>
                              {formatDate(leave.start_date)} –{" "}
                              {formatDate(leave.end_date)}
                            </td>
                            <td>{getLeaveDays(leave)}</td>
                            <td>
                              <StatusBadge status={leave.status || "pending"} />
                            </td>
                            <td>
                              {user?.role !== "employee" && leave.status?.toLowerCase() === "pending" ? (
                                <div className="leave-review-actions">
                                  <button
                                    type="button"
                                    className="button button-primary button-small"
                                    disabled={leaveActionId !== null}
                                    onClick={() => reviewLeave(leave.id, "approved")}
                                  >
                                    {leaveActionId === leave.id ? "Saving..." : "Approve"}
                                  </button>
                                  <button
                                    type="button"
                                    className="button button-secondary button-small"
                                    disabled={leaveActionId !== null}
                                    onClick={() => reviewLeave(leave.id, "rejected")}
                                  >
                                    Reject
                                  </button>
                                </div>
                              ) : user?.role === "employee" ? (
                                <span className="report-muted">Your request</span>
                              ) : (
                                <span className="report-muted">Already reviewed</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </>
    );
  }


  
  function renderPayroll() {
    const currentMonth = new Date().toISOString().slice(0, 7);

    const currentMonthRecords = payroll.filter(
      (record) => String(record.pay_period).slice(0, 7) === currentMonth
    );

    const monthlyTotal = currentMonthRecords.reduce(
      (total, record) => total + Number(record.net_salary || 0),
      0
    );

    const formatPeriod = (value) => {
      if (!value) return "—";

      const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);

      return Number.isNaN(date.getTime())
        ? String(value)
        : date.toLocaleDateString("en-IN", {
            month: "short",
            year: "numeric",
          });
    };

    const getEmployee = (record) =>
      employees.find((employee) => employee.id === record.employee_id);

    return (
      <>
        <div className="page-intro">
          <div>
            <div className="eyebrow">COMPENSATION</div>
            <h1>Payroll</h1>
            <p className="page-description">
              Review salary components and payroll summaries.
            </p>
          </div>
        </div>

        {payrollLoading && (
          <div className="demo-banner">
            <FileText size={16} />
            <span>Loading payroll records...</span>
          </div>
        )}

        {payrollError && (
          <div className="dashboard-error">
            {payrollError}
            <button onClick={loadPayroll}>Retry</button>
          </div>
        )}

        {!payrollLoading && !payrollError && (
          <>
            <section className="stats-grid">
              <StatCard
                title="Monthly payroll"
                value={
                  payrollLoaded ? formatCurrency(monthlyTotal) : "—"
                }
                note="Current month net salaries"
                icon={Wallet}
                variant="blue"
              />
              <StatCard
                title="Processed records"
                value={
                  payrollLoaded ? String(currentMonthRecords.length) : "—"
                }
                note="Current month records"
                icon={CheckCircle2}
                variant="green"
              />
              <StatCard
                title="Pending records"
                value="—"
                note="No payroll processing status available"
                icon={Clock3}
                variant="orange"
              />
              <StatCard
                title="Pay period"
                value={formatPeriod(`${currentMonth}-01`)}
                note="Current calendar month"
                icon={CalendarDays}
                variant="purple"
              />
            </section>

            <section className="panel page-panel">
              <SectionHeading
                title="Payroll records"
                subtitle={`${payroll.length} live record(s) from the database`}
              />

              {payroll.length === 0 ? (
                <div className="dashboard-empty">
                  No payroll records found.
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>EMPLOYEE</th>
                        <th>PERIOD</th>
                        <th>BASIC</th>
                        <th>ALLOWANCES</th>
                        <th>DEDUCTIONS</th>
                        <th>NET SALARY</th>
                      </tr>
                    </thead>
                    <tbody>
                      {payroll.map((record) => {
                        const employee = getEmployee(record);
                        const employeeName = employee
                          ? getEmployeeName(employee)
                          : `Employee #${record.employee_id}`;

                        return (
                          <tr key={record.id}>
                            <td>
                              <div className="employee-identity">
                                <Avatar name={employeeName} />
                                <div>
                                  <strong>{employeeName}</strong>
                                  <span>#{record.employee_id}</span>
                                </div>
                              </div>
                            </td>
                            <td>{formatPeriod(record.pay_period)}</td>
                            <td>{formatCurrency(Number(record.basic_salary || 0))}</td>
                            <td>{formatCurrency(Number(record.allowances || 0))}</td>
                            <td>{formatCurrency(Number(record.deductions || 0))}</td>
                            <td>
                              <strong className="salary-value">
                                {formatCurrency(Number(record.net_salary || 0))}
                              </strong>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </>
    );
  }


  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">H</div>
          <div className="brand-copy">
            <strong>HORIZON</strong>
            <span>HUMAN RESOURCES</span>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="navigation" aria-label="Main navigation">
          {navigation.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${activePage === label ? "nav-active" : ""}`}
              onClick={() => openPage(label)}
            >
              <Icon size={18} strokeWidth={1.8} />
              <span>{label}</span>
              {label === "Leave Management" && (
                <span className="nav-counter">{leaves.filter((leave) => leave.status?.toLowerCase() === "pending").length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-divider" />
          <div className="sidebar-profile">
            <Avatar name={displayName} />
            <div className="profile-copy">
              <strong>{displayName}</strong>
              <span>{user?.role || "Authenticated user"}</span>
            </div>
            <button
              className="profile-menu"
              onClick={onLogout}
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span>/</span>
            <strong>{activePage}</strong>
          </div>

          <div className="topbar-right">
            <label className="search-box">
              <Search size={17} />
              <input
                placeholder={
                  activePage === "Employees"
                    ? "Search employees..."
                    : "Search employees..."
                }
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                aria-label="Search employees"
              />
              {search && (
                <button
                  type="button"
                  className="search-clear"
                  aria-label="Clear search"
                  onClick={() => setSearch("")}
                >
                  <X size={14} />
                </button>
              )}
            </label>
            <div className="notification-wrapper">
              <button
                type="button"
                className="notification-button"
                aria-label="Notifications"
                title="Notifications"
                aria-expanded={showNotifications}
                onClick={() => setShowNotifications((current) => !current)}
              >
                <Bell size={18} strokeWidth={1.8} />
                {leavesLoaded && leaves.filter((leave) => leave.status?.toLowerCase() === "pending").length > 0 && (
                  <span className="notification-dot" aria-hidden="true" />
                )}
              </button>

              {showNotifications && (
                <section className="notification-panel" aria-label="Notifications panel">
                  <div className="notification-panel-heading">
                    <strong>Notifications</strong>
                    <button
                      type="button"
                      className="icon-button"
                      aria-label="Close notifications"
                      onClick={() => setShowNotifications(false)}
                    >
                      <X size={15} />
                    </button>
                  </div>

                  {!leavesLoaded && leavesLoading ? (
                    <p className="notification-message">Loading leave requests...</p>
                  ) : leavesError ? (
                    <div className="notification-message">
                      <p>{leavesError}</p>
                      <button type="button" className="button button-secondary" onClick={loadLeaves}>
                        Retry
                      </button>
                    </div>
                  ) : !leavesLoaded ? (
                    <div className="notification-message">
                      <p>Leave notifications have not loaded yet.</p>
                      <button type="button" className="button button-secondary" onClick={loadLeaves}>
                        Load notifications
                      </button>
                    </div>
                  ) : leaves.filter((leave) => leave.status?.toLowerCase() === "pending").length === 0 ? (
                    <p className="notification-message">You're all caught up. No pending leave requests.</p>
                  ) : (
                    <div className="notification-list">
                      {leaves
                        .filter((leave) => leave.status?.toLowerCase() === "pending")
                        .slice(0, 5)
                        .map((leave) => (
                          <div className="notification-item" key={leave.id}>
                            <span className="notification-item-icon">
                              <ClipboardCheck size={16} />
                            </span>
                            <div>
                              <strong>Leave request pending</strong>
                              <p>
                                Employee #{leave.employee_id} · {(leave.leave_type || "Leave").replaceAll("_", " ")}
                              </p>
                              <span>
                                {String(leave.start_date || "").slice(0, 10)}
                                {leave.end_date && leave.end_date !== leave.start_date
                                  ? ` – ${String(leave.end_date).slice(0, 10)}`
                                  : ""}
                              </span>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}

                  <button
                    type="button"
                    className="notification-view-all"
                    onClick={() => {
                      setShowNotifications(false);
                      openPage("Leave Management");
                    }}
                  >
                    View leave management <ArrowUpRight size={15} />
                  </button>
                </section>
              )}
            </div>
          </div>
        </header>

        <div className="page-content">
          {activePage === "Dashboard" && renderDashboard()}
          {activePage === "Employees" && renderEmployees()}
          {activePage === "Attendance" && renderAttendance()}
          {activePage === "Leave Management" && renderLeaveManagement()}
          {activePage === "Payroll" && renderPayroll()}
          {activePage === "Reports" && renderReports()}
        </div>

        <footer className="app-footer">
          <span>Horizon HRMS</span>
          <span>Workforce management platform</span>
        </footer>
      </main>
    </div>
  );
}
