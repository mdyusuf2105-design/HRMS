import { useEffect, useState } from "react";
import {
  CalendarDays,
  Clock3,
  Calculator,
  RefreshCw,
  Plus,
  Users,
} from "lucide-react";
import api from "../api/client";

const todayString = () => new Date().toISOString().slice(0, 10);

export default function WorkforceManagement({ user }) {
  const isAdminOrHR = ["admin", "hr"].includes(
    String(user?.role || "").toLowerCase()
  );

  const [section, setSection] = useState("holidays");
  const [holidays, setHolidays] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [holidayForm, setHolidayForm] = useState({
    name: "",
    holiday_date: todayString(),
    holiday_type: "company",
    region: "",
    description: "",
    is_active: true,
  });

  const [editingHolidayId, setEditingHolidayId] = useState(null);

  const [shiftForm, setShiftForm] = useState({
    name: "",
    start_time: "09:00",
    end_time: "18:00",
    grace_period_minutes: 10,
    is_active: true,
  });

  const [editingShiftId, setEditingShiftId] = useState(null);

  const [assignmentForm, setAssignmentForm] = useState({
    employee_id: "",
    shift_id: "",
  });

  const [employeeLookupId, setEmployeeLookupId] = useState("");
  const [employeeShiftResults, setEmployeeShiftResults] = useState([]);

  const [calculator, setCalculator] = useState({
    start_date: todayString(),
    end_date: todayString(),
    region: "",
  });
  const [calculation, setCalculation] = useState(null);

  async function loadHolidays() {
    const response = await api.get("/holidays/");
    setHolidays(response.data);
  }

  async function loadShifts() {
    const response = await api.get("/shifts/");
    setShifts(response.data);
  }

  async function loadEmployees() {
    if (!isAdminOrHR) return;
    const response = await api.get("/employees/");
    setEmployees(Array.isArray(response.data) ? response.data : []);
  }

  async function refreshData() {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      await Promise.all([loadHolidays(), loadShifts(), loadEmployees()]);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load workforce data. Check your access and backend connection."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshData();
    // Refresh when the signed-in user's role changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdminOrHR]);

  function clearHolidayForm() {
    setHolidayForm({
      name: "",
      holiday_date: todayString(),
      holiday_type: "company",
      region: "",
      description: "",
      is_active: true,
    });
    setEditingHolidayId(null);
  }

  async function saveHoliday(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    const payload = {
      ...holidayForm,
      name: holidayForm.name.trim(),
      region:
        holidayForm.holiday_type === "regional"
          ? holidayForm.region.trim()
          : null,
      description: holidayForm.description.trim() || null,
    };

    try {
      if (editingHolidayId) {
        await api.patch(`/holidays/${editingHolidayId}`, payload);
        setMessage("Holiday updated successfully.");
      } else {
        await api.post("/holidays/", payload);
        setMessage("Holiday created successfully.");
      }
      clearHolidayForm();
      await loadHolidays();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to save holiday.");
    }
  }

  function editHoliday(holiday) {
    setEditingHolidayId(holiday.id);
    setHolidayForm({
      name: holiday.name || "",
      holiday_date: String(holiday.holiday_date).slice(0, 10),
      holiday_type: holiday.holiday_type || "company",
      region: holiday.region || "",
      description: holiday.description || "",
      is_active: holiday.is_active,
    });
    setMessage("");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function deactivateHoliday(holiday) {
    if (!window.confirm(`Deactivate "${holiday.name}"?`)) return;

    setError("");
    setMessage("");

    try {
      await api.delete(`/holidays/${holiday.id}`);
      setMessage("Holiday deactivated.");
      await loadHolidays();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to deactivate holiday.");
    }
  }

  function clearShiftForm() {
    setShiftForm({
      name: "",
      start_time: "09:00",
      end_time: "18:00",
      grace_period_minutes: 10,
      is_active: true,
    });
    setEditingShiftId(null);
  }

  async function saveShift(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    const payload = {
      ...shiftForm,
      name: shiftForm.name.trim(),
      start_time: `${shiftForm.start_time}:00`.slice(0, 8),
      end_time: `${shiftForm.end_time}:00`.slice(0, 8),
      grace_period_minutes: Number(shiftForm.grace_period_minutes),
    };

    try {
      if (editingShiftId) {
        await api.patch(`/shifts/${editingShiftId}`, payload);
        setMessage("Shift updated successfully.");
      } else {
        await api.post("/shifts/", payload);
        setMessage("Shift created successfully.");
      }
      clearShiftForm();
      await loadShifts();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to save shift.");
    }
  }

  function editShift(shift) {
    setEditingShiftId(shift.id);
    setShiftForm({
      name: shift.name || "",
      start_time: String(shift.start_time).slice(0, 5),
      end_time: String(shift.end_time).slice(0, 5),
      grace_period_minutes: shift.grace_period_minutes ?? 10,
      is_active: shift.is_active,
    });
    setMessage("");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function deactivateShift(shift) {
    if (!window.confirm(`Deactivate "${shift.name}"?`)) return;

    setError("");
    setMessage("");

    try {
      await api.delete(`/shifts/${shift.id}`);
      setMessage("Shift deactivated.");
      await loadShifts();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to deactivate shift.");
    }
  }

  async function assignShift(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    try {
      const response = await api.post("/shifts/assignments", {
        employee_id: Number(assignmentForm.employee_id),
        shift_id: Number(assignmentForm.shift_id),
      });
      setMessage(
        `Shift assigned successfully. Assignment ID: ${response.data.id}`
      );
      setAssignmentForm({ employee_id: "", shift_id: "" });
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to assign shift.");
    }
  }

  async function lookupEmployeeShifts(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setEmployeeShiftResults([]);

    try {
      const response = await api.get(
        `/shifts/assignments/employee/${Number(employeeLookupId)}`
      );
      setEmployeeShiftResults(response.data);
      setMessage("Employee shift assignments loaded.");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to load employee shift assignments."
      );
    }
  }

  async function calculateWorkingDays(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setCalculation(null);

    if (calculator.end_date < calculator.start_date) {
      setError("End date cannot be before start date.");
      return;
    }

    try {
      const response = await api.get("/working-days/", {
        params: {
          start_date: calculator.start_date,
          end_date: calculator.end_date,
          ...(calculator.region.trim()
            ? { region: calculator.region.trim() }
            : {}),
        },
      });
      setCalculation(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to calculate working days. Please check the dates and region."
      );
    }
  }

  const employeeName = (employee) =>
    employee.name ||
    employee.full_name ||
    [employee.first_name, employee.last_name].filter(Boolean).join(" ") ||
    employee.email ||
    `Employee #${employee.id}`;

  return (
    <section className="workforce-management">
      <div className="section-heading">
        <div>
          <h2>Workforce Management</h2>
          <p>Manage holidays, shifts, assignments and working-day calculations.</p>
        </div>
        <button
          className="button button-secondary"
          type="button"
          onClick={refreshData}
          disabled={loading}
        >
          <RefreshCw size={16} />
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="workforce-tabs" role="tablist" aria-label="Workforce modules">
        <button
          type="button"
          className={section === "holidays" ? "workforce-tab active" : "workforce-tab"}
          onClick={() => setSection("holidays")}
        >
          <CalendarDays size={16} /> Holidays
        </button>
        <button
          type="button"
          className={section === "shifts" ? "workforce-tab active" : "workforce-tab"}
          onClick={() => setSection("shifts")}
        >
          <Clock3 size={16} /> Shifts
        </button>
        <button
          type="button"
          className={section === "working-days" ? "workforce-tab active" : "workforce-tab"}
          onClick={() => setSection("working-days")}
        >
          <Calculator size={16} /> Working Days
        </button>
      </div>

      {error && <div className="workforce-alert error" role="alert">{String(error)}</div>}
      {message && <div className="workforce-alert success" role="status">{message}</div>}

      {section === "holidays" && (
        <>
          {isAdminOrHR && (
            <section className="workforce-panel">
              <h3>{editingHolidayId ? "Edit holiday" : "Add a holiday"}</h3>
              <form className="workforce-form" onSubmit={saveHoliday}>
                <label>
                  Holiday name
                  <input
                    required
                    maxLength={100}
                    value={holidayForm.name}
                    onChange={(e) => setHolidayForm({ ...holidayForm, name: e.target.value })}
                    placeholder="e.g. Republic Day"
                  />
                </label>
                <label>
                  Date
                  <input
                    required
                    type="date"
                    value={holidayForm.holiday_date}
                    onChange={(e) => setHolidayForm({ ...holidayForm, holiday_date: e.target.value })}
                  />
                </label>
                <label>
                  Type
                  <select
                    value={holidayForm.holiday_type}
                    onChange={(e) => setHolidayForm({ ...holidayForm, holiday_type: e.target.value })}
                  >
                    <option value="company">Company-wide</option>
                    <option value="regional">Regional</option>
                    <option value="optional">Optional</option>
                  </select>
                </label>
                {holidayForm.holiday_type === "regional" && (
                  <label>
                    Region
                    <input
                      required
                      value={holidayForm.region}
                      onChange={(e) => setHolidayForm({ ...holidayForm, region: e.target.value })}
                      placeholder="e.g. Tamil Nadu"
                    />
                  </label>
                )}
                <label className="workforce-wide">
                  Description
                  <textarea
                    rows={2}
                    value={holidayForm.description}
                    onChange={(e) => setHolidayForm({ ...holidayForm, description: e.target.value })}
                    placeholder="Optional details"
                  />
                </label>
                <div className="workforce-actions workforce-wide">
                  <button className="button button-primary" type="submit">
                    <Plus size={16} /> {editingHolidayId ? "Save changes" : "Create holiday"}
                  </button>
                  {editingHolidayId && (
                    <button className="button button-secondary" type="button" onClick={clearHolidayForm}>
                      Cancel edit
                    </button>
                  )}
                </div>
              </form>
            </section>
          )}

          <section className="workforce-panel">
            <h3>Holiday calendar</h3>
            {loading && holidays.length === 0 ? (
              <p>Loading holidays...</p>
            ) : holidays.length === 0 ? (
              <p className="dashboard-empty">No active holidays found.</p>
            ) : (
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>HOLIDAY</th>
                      <th>DATE</th>
                      <th>TYPE</th>
                      <th>REGION</th>
                      {isAdminOrHR && <th>ACTIONS</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {holidays.map((holiday) => (
                      <tr key={holiday.id}>
                        <td>
                          <strong>{holiday.name}</strong>
                          {holiday.description && <div>{holiday.description}</div>}
                        </td>
                        <td>{String(holiday.holiday_date).slice(0, 10)}</td>
                        <td>{holiday.holiday_type}</td>
                        <td>{holiday.region || "All regions"}</td>
                        {isAdminOrHR && (
                          <td>
                            <div className="workforce-actions">
                              <button className="button button-secondary" type="button" onClick={() => editHoliday(holiday)}>
                                Edit
                              </button>
                              {holiday.is_active && (
                                <button className="button button-secondary" type="button" onClick={() => deactivateHoliday(holiday)}>
                                  Deactivate
                                </button>
                              )}
                            </div>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}

      {section === "shifts" && (
        <>
          {isAdminOrHR && (
            <>
              <section className="workforce-panel">
                <h3>{editingShiftId ? "Edit shift" : "Create a shift"}</h3>
                <form className="workforce-form" onSubmit={saveShift}>
                  <label>
                    Shift name
                    <input
                      required
                      maxLength={100}
                      value={shiftForm.name}
                      onChange={(e) => setShiftForm({ ...shiftForm, name: e.target.value })}
                      placeholder="e.g. General Shift"
                    />
                  </label>
                  <label>
                    Start time
                    <input
                      required
                      type="time"
                      value={shiftForm.start_time}
                      onChange={(e) => setShiftForm({ ...shiftForm, start_time: e.target.value })}
                    />
                  </label>
                  <label>
                    End time
                    <input
                      required
                      type="time"
                      value={shiftForm.end_time}
                      onChange={(e) => setShiftForm({ ...shiftForm, end_time: e.target.value })}
                    />
                  </label>
                  <label>
                    Grace period (minutes)
                    <input
                      required
                      type="number"
                      min="0"
                      max="180"
                      value={shiftForm.grace_period_minutes}
                      onChange={(e) => setShiftForm({ ...shiftForm, grace_period_minutes: e.target.value })}
                    />
                  </label>
                  <div className="workforce-actions workforce-wide">
                    <button className="button button-primary" type="submit">
                      <Plus size={16} /> {editingShiftId ? "Save changes" : "Create shift"}
                    </button>
                    {editingShiftId && (
                      <button className="button button-secondary" type="button" onClick={clearShiftForm}>
                        Cancel edit
                      </button>
                    )}
                  </div>
                </form>
              </section>

              <section className="workforce-panel">
                <h3>Assign a shift</h3>
                <form className="workforce-form" onSubmit={assignShift}>
                  <label>
                    Employee
                    <select
                      required
                      value={assignmentForm.employee_id}
                      onChange={(e) => setAssignmentForm({ ...assignmentForm, employee_id: e.target.value })}
                    >
                      <option value="">Select employee</option>
                      {employees.map((employee) => (
                        <option key={employee.id} value={employee.id}>
                          {employeeName(employee)} — #{employee.id}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Active shift
                    <select
                      required
                      value={assignmentForm.shift_id}
                      onChange={(e) => setAssignmentForm({ ...assignmentForm, shift_id: e.target.value })}
                    >
                      <option value="">Select shift</option>
                      {shifts.filter((shift) => shift.is_active).map((shift) => (
                        <option key={shift.id} value={shift.id}>
                          {shift.name} ({String(shift.start_time).slice(0, 5)}–{String(shift.end_time).slice(0, 5)})
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="workforce-actions workforce-wide">
                    <button className="button button-primary" type="submit">
                      <Users size={16} /> Assign shift
                    </button>
                  </div>
                </form>
              </section>
            </>
          )}

          <section className="workforce-panel">
            <h3>Available shifts</h3>
            {shifts.length === 0 ? (
              <p className="dashboard-empty">No active shifts found.</p>
            ) : (
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>SHIFT</th>
                      <th>START</th>
                      <th>END</th>
                      <th>GRACE</th>
                      <th>STATUS</th>
                      {isAdminOrHR && <th>ACTIONS</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {shifts.map((shift) => (
                      <tr key={shift.id}>
                        <td><strong>{shift.name}</strong></td>
                        <td>{String(shift.start_time).slice(0, 5)}</td>
                        <td>{String(shift.end_time).slice(0, 5)}</td>
                        <td>{shift.grace_period_minutes} min</td>
                        <td>{shift.is_active ? "Active" : "Inactive"}</td>
                        {isAdminOrHR && (
                          <td>
                            <div className="workforce-actions">
                              <button className="button button-secondary" type="button" onClick={() => editShift(shift)}>
                                Edit
                              </button>
                              {shift.is_active && (
                                <button className="button button-secondary" type="button" onClick={() => deactivateShift(shift)}>
                                  Deactivate
                                </button>
                              )}
                            </div>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {isAdminOrHR && (
            <section className="workforce-panel">
              <h3>View employee assignments</h3>
              <form className="workforce-form" onSubmit={lookupEmployeeShifts}>
                <label>
                  Employee ID
                  <input
                    type="number"
                    min="1"
                    required
                    value={employeeLookupId}
                    onChange={(e) => setEmployeeLookupId(e.target.value)}
                    placeholder="Enter employee ID"
                  />
                </label>
                <div className="workforce-actions workforce-wide">
                  <button className="button button-secondary" type="submit">View assignments</button>
                </div>
              </form>
              {employeeShiftResults.length > 0 && (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr><th>ASSIGNMENT ID</th><th>EMPLOYEE</th><th>SHIFT ID</th><th>ASSIGNED AT</th></tr>
                    </thead>
                    <tbody>
                      {employeeShiftResults.map((item) => (
                        <tr key={item.id}>
                          <td>{item.id}</td>
                          <td>{item.employee_id}</td>
                          <td>{item.shift_id}</td>
                          <td>{String(item.assigned_at).replace("T", " ").slice(0, 19)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {employeeShiftResults.length === 0 && employeeLookupId && (
                <p>No assignments loaded, or this employee has no assignments.</p>
              )}
            </section>
          )}
        </>
      )}

      {section === "working-days" && (
        <section className="workforce-panel">
          <h3>Working-day calculator</h3>
          <p>Calculate working days after excluding weekends and applicable company/regional holidays.</p>
          <form className="workforce-form" onSubmit={calculateWorkingDays}>
            <label>
              Start date
              <input
                type="date"
                required
                value={calculator.start_date}
                onChange={(e) => setCalculator({ ...calculator, start_date: e.target.value })}
              />
            </label>
            <label>
              End date
              <input
                type="date"
                required
                value={calculator.end_date}
                onChange={(e) => setCalculator({ ...calculator, end_date: e.target.value })}
              />
            </label>
            <label>
              Region (optional)
              <input
                value={calculator.region}
                onChange={(e) => setCalculator({ ...calculator, region: e.target.value })}
                placeholder="e.g. Tamil Nadu"
              />
            </label>
            <div className="workforce-actions workforce-wide">
              <button className="button button-primary" type="submit">
                <Calculator size={16} /> Calculate working days
              </button>
            </div>
          </form>

          {calculation && (
            <div className="workforce-results">
              <div><span>Calendar days</span><strong>{calculation.total_calendar_days}</strong></div>
              <div><span>Weekend days</span><strong>{calculation.weekend_days}</strong></div>
              <div><span>Applicable holidays</span><strong>{calculation.applicable_holiday_days}</strong></div>
              <div><span>Working days</span><strong>{calculation.working_days}</strong></div>
              <p>
                Period: {calculation.start_date} to {calculation.end_date}
              </p>
            </div>
          )}
        </section>
      )}
    </section>
  );
}
