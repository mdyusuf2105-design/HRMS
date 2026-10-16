import { useEffect, useMemo, useState } from "react";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  CalendarRange,
  RefreshCw,
} from "lucide-react";
import api from "../api/client";

const today = new Date();
const dateKey = (value) => {
  if (!value) return "";
  const match = String(value).match(/^(\d{4}-\d{2}-\d{2})/);
  return match ? match[1] : "";
};

const arrayFrom = (data) => {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.results)) return data.results;
  return [];
};

const eventDate = (item) =>
  dateKey(
    item.holiday_date ||
    item.attendance_date ||
    item.date ||
    item.check_in_date ||
    item.created_at
  );

const eventName = (item) =>
  item.name ||
  item.title ||
  item.full_name ||
  item.employee_name ||
  item.type ||
  "Event";

const colors = {
  Holiday: "#16805d",
  Attendance: "#3769c8",
  Leave: "#a15bc0",
};

export default function CalendarView() {
  const [view, setView] = useState("month");
  const [displayDate, setDisplayDate] = useState(
    new Date(today.getFullYear(), today.getMonth(), 1)
  );
  const [selectedDate, setSelectedDate] = useState(
    `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`
  );
  const [holidays, setHolidays] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadCalendar() {
      setLoading(true);
      setError("");

      const results = await Promise.allSettled([
        api.get("/holidays/"),
        api.get("/attendance/"),
        api.get("/leaves/"),
      ]);

      if (cancelled) return;

      const [holidayResult, attendanceResult, leaveResult] = results;

      if (holidayResult.status === "fulfilled") {
        setHolidays(arrayFrom(holidayResult.value.data));
      } else {
        setHolidays([]);
        setError(
          holidayResult.reason?.response?.data?.detail ||
          "Holiday records could not be loaded."
        );
      }

      setAttendance(
        attendanceResult.status === "fulfilled"
          ? arrayFrom(attendanceResult.value.data)
          : []
      );

      setLeaves(
        leaveResult.status === "fulfilled"
          ? arrayFrom(leaveResult.value.data)
          : []
      );

      setLoading(false);
    }

    loadCalendar();
    return () => {
      cancelled = true;
    };
  }, []);

  const events = useMemo(() => {
    const result = [];

    holidays.forEach((item) => {
      if (item.is_active === false) return;
      const date = eventDate(item);
      if (date) {
        result.push({
          date,
          title: eventName(item),
          type: "Holiday",
          detail: [
            item.holiday_type,
            item.region,
            item.description,
          ].filter(Boolean).join(" · "),
        });
      }
    });

    attendance.forEach((item) => {
      const date = eventDate(item);
      if (date) {
        result.push({
          date,
          title: "Attendance",
          type: "Attendance",
          detail: [
            item.status,
            item.check_in ? `In: ${String(item.check_in).slice(11, 16)}` : "",
            item.check_out ? `Out: ${String(item.check_out).slice(11, 16)}` : "",
          ].filter(Boolean).join(" · "),
        });
      }
    });

    leaves.forEach((item) => {
      if (String(item.status || "").toLowerCase() !== "approved") return;

      const start = dateKey(
        item.start_date || item.from_date || item.leave_start_date
      );
      const end = dateKey(
        item.end_date || item.to_date || item.leave_end_date || start
      );

      if (!start) {
        const date = eventDate(item);
        if (date) {
          result.push({
            date,
            title: item.leave_type || item.type || "Leave",
            type: "Leave",
            detail: "Approved leave",
          });
        }
        return;
      }

      const cursor = new Date(`${start}T12:00:00`);
      const last = new Date(`${end || start}T12:00:00`);
      let count = 0;

      while (cursor <= last && count < 370) {
        const date = `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, "0")}-${String(cursor.getDate()).padStart(2, "0")}`;
        result.push({
          date,
          title: item.leave_type || item.type || "Approved leave",
          type: "Leave",
          detail: "Approved leave",
        });
        cursor.setDate(cursor.getDate() + 1);
        count += 1;
      }
    });

    return result;
  }, [holidays, attendance, leaves]);

  const eventsByDate = useMemo(() => {
    const grouped = {};
    events.forEach((event) => {
      if (!grouped[event.date]) grouped[event.date] = [];
      grouped[event.date].push(event);
    });
    return grouped;
  }, [events]);

  const year = displayDate.getFullYear();
  const month = displayDate.getMonth();
  const monthName = displayDate.toLocaleDateString("en", {
    month: "long",
    year: "numeric",
  });

  const changeMonth = (amount) => {
    setDisplayDate(new Date(year, month + amount, 1));
  };

  const changeYear = (amount) => {
    setDisplayDate(new Date(year + amount, month, 1));
  };

  const monthCells = useMemo(() => {
    const firstDay = new Date(year, month, 1).getDay();
    const totalDays = new Date(year, month + 1, 0).getDate();
    const previousMonthDays = new Date(year, month, 0).getDate();

    return Array.from({ length: 42 }, (_, index) => {
      const dayNumber = index - firstDay + 1;
      if (dayNumber < 1) {
        return {
          day: previousMonthDays + dayNumber,
          date: `${new Date(year, month - 1, 1).getFullYear()}-${String(new Date(year, month - 1, 1).getMonth() + 1).padStart(2, "0")}-${String(previousMonthDays + dayNumber).padStart(2, "0")}`,
          outside: true,
        };
      }
      if (dayNumber > totalDays) {
        const nextDate = new Date(year, month + 1, dayNumber - totalDays);
        return {
          day: dayNumber - totalDays,
          date: `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, "0")}-${String(nextDate.getDate()).padStart(2, "0")}`,
          outside: true,
        };
      }
      return {
        day: dayNumber,
        date: `${year}-${String(month + 1).padStart(2, "0")}-${String(dayNumber).padStart(2, "0")}`,
        outside: false,
      };
    });
  }, [year, month]);

  const selectedEvents = eventsByDate[selectedDate] || [];
  const yearMonths = Array.from({ length: 12 }, (_, index) => {
    const date = new Date(year, index, 1);
    return {
      index,
      name: date.toLocaleDateString("en", { month: "long" }),
      short: date.toLocaleDateString("en", { month: "short" }),
      days: new Date(year, index + 1, 0).getDate(),
      offset: date.getDay(),
    };
  });

  const changeView = (nextView) => {
    setView(nextView);
    setDisplayDate(new Date(year, month, 1));
  };

  return (
    <section className="calendar-page">
      <div className="calendar-heading">
        <div>
          <div className="calendar-eyebrow">WORKFORCE PLANNING</div>
          <h1>Calendar</h1>
          <p>View company holidays, attendance and approved leave dates.</p>
        </div>
        <div className="calendar-view-switch">
          <button
            className={view === "month" ? "calendar-view-active" : ""}
            onClick={() => changeView("month")}
          >
            <CalendarDays size={16} /> Monthly
          </button>
          <button
            className={view === "year" ? "calendar-view-active" : ""}
            onClick={() => changeView("year")}
          >
            <CalendarRange size={16} /> Yearly
          </button>
        </div>
      </div>

      <div className="calendar-legend">
        {Object.entries(colors).map(([name, color]) => (
          <span key={name}>
            <i style={{ background: color }} /> {name}
          </span>
        ))}
      </div>

      <div className="calendar-panel">
        <div className="calendar-toolbar">
          <button
            aria-label={view === "month" ? "Previous month" : "Previous year"}
            onClick={() => view === "month" ? changeMonth(-1) : changeYear(-1)}
          >
            <ChevronLeft size={19} />
          </button>
          <h2>{view === "month" ? monthName : year}</h2>
          <button
            aria-label={view === "month" ? "Next month" : "Next year"}
            onClick={() => view === "month" ? changeMonth(1) : changeYear(1)}
          >
            <ChevronRight size={19} />
          </button>
          <button
            className="calendar-today-button"
            onClick={() => {
              setDisplayDate(new Date(today.getFullYear(), today.getMonth(), 1));
              setSelectedDate(
                `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`
              );
            }}
          >
            Today
          </button>
        </div>

        {loading && (
          <div className="calendar-message">
            <RefreshCw size={17} /> Loading calendar data…
          </div>
        )}
        {error && <div className="calendar-error">{error}</div>}

        {view === "month" ? (
          <div className="calendar-month-grid">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div className="calendar-weekday" key={day}>{day}</div>
            ))}
            {monthCells.map((cell) => {
              const dayEvents = eventsByDate[cell.date] || [];
              const isToday = cell.date === dateKey(today.toISOString());
              return (
                <button
                  key={cell.date}
                  className={[
                    "calendar-day",
                    cell.outside ? "calendar-day-outside" : "",
                    selectedDate === cell.date ? "calendar-day-selected" : "",
                    isToday ? "calendar-day-today" : "",
                  ].filter(Boolean).join(" ")}
                  onClick={() => {
                    setSelectedDate(cell.date);
                    if (cell.outside) {
                      const [y, m] = cell.date.split("-").map(Number);
                      setDisplayDate(new Date(y, m - 1, 1));
                    }
                  }}
                >
                  <span className="calendar-day-number">{cell.day}</span>
                  <span className="calendar-day-events">
                    {dayEvents.slice(0, 2).map((event, index) => (
                      <span
                        key={`${event.type}-${index}`}
                        className="calendar-event-dot"
                        style={{ background: colors[event.type] }}
                        title={event.title}
                      />
                    ))}
                    {dayEvents.length > 2 && (
                      <span className="calendar-more">+{dayEvents.length - 2}</span>
                    )}
                  </span>
                  {dayEvents.slice(0, 1).map((event, index) => (
                    <span
                      key={index}
                      className="calendar-event-label"
                      style={{ color: colors[event.type] }}
                    >
                      {event.title}
                    </span>
                  ))}
                </button>
              );
            })}
          </div>
        ) : (
          <div className="calendar-year-grid">
            {yearMonths.map((item) => (
              <button
                key={item.index}
                className="calendar-year-month"
                onClick={() => {
                  setDisplayDate(new Date(year, item.index, 1));
                  setView("month");
                }}
              >
                <strong>{item.name}</strong>
                <div className="calendar-mini-grid">
                  {Array.from({ length: item.offset + item.days }, (_, index) => {
                    if (index < item.offset) {
                      return <span key={`empty-${index}`} />;
                    }
                    const day = index - item.offset + 1;
                    const key = `${year}-${String(item.index + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                    const hasEvents = Boolean(eventsByDate[key]?.length);
                    return (
                      <span
                        key={day}
                        className={hasEvents ? "calendar-mini-event" : ""}
                        title={hasEvents ? eventsByDate[key].map((event) => event.title).join(", ") : ""}
                      >
                        {day}
                      </span>
                    );
                  })}
                </div>
                <small>
                  {events.filter((event) => event.date.startsWith(`${year}-${String(item.index + 1).padStart(2, "0")}-`)).length} events
                </small>
              </button>
            ))}
          </div>
        )}
      </div>

      {view === "month" && (
        <section className="calendar-details">
          <div className="calendar-details-heading">
            <div>
              <h2>{selectedDate}</h2>
              <p>{selectedEvents.length} event{selectedEvents.length === 1 ? "" : "s"} on this date</p>
            </div>
          </div>
          {selectedEvents.length ? (
            <div className="calendar-event-list">
              {selectedEvents.map((event, index) => (
                <article className="calendar-event-card" key={`${event.type}-${index}`}>
                  <i style={{ background: colors[event.type] }} />
                  <div>
                    <strong>{event.title}</strong>
                    <span>{event.type}{event.detail ? ` · ${event.detail}` : ""}</span>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="calendar-empty">No recorded events for this date.</div>
          )}
        </section>
      )}
    </section>
  );
}
