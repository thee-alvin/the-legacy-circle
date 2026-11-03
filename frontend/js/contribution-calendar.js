(() => {
"use strict";

const root = document.getElementById("contributionCalendarApp");
if (!root || root.dataset.initialized === "true") return;
root.dataset.initialized = "true";

const byId = id => document.getElementById(id);
const notice = byId("calendarNotice");
const workspace = byId("calendarWorkspace");
const grid = byId("calendarGrid");

const statusInfo = {
    PAID: {label:"Paid", badge:"Paid", css:"status-paid",
        note:"A confirmed TLC coverage allocation covers this contribution week."},
    UNPAID: {label:"Unpaid", badge:"Unpaid", css:"status-unpaid",
        note:"This Thursday has passed and no valid coverage allocation was found. Contact TLC Treasury if you have already paid."},
    UPCOMING: {label:"Upcoming", badge:"Upcoming", css:"status-upcoming",
        note:"This Thursday is in the future and is not currently covered by the records read by the calendar."},
    NOT_DUE: {label:"Not due", badge:"Not due", css:"status-not-due",
        note:"This date is before the contribution start date calculated for your account."},
    START_DATE_REQUIRED: {label:"Needs review", badge:"Review", css:"status-review",
        note:"The available data does not establish your contribution start date. Ask TLC Treasury to verify it."}
};

const money = new Intl.NumberFormat("en-KE", {
    style:"currency", currency:"KES", minimumFractionDigits:2, maximumFractionDigits:2
});
const today = new Date();
let year = today.getFullYear();
let month = today.getMonth() + 1;
let selectedDate = null;
let loadedCalendar = null;
let requestId = 0;

function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = String(text);
    return element;
}
function dateKey(y,m,d) {
    return `${String(y).padStart(4,"0")}-${String(m).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
}
function longDate(value) {
    const [y,m,d] = String(value).split("-").map(Number);
    return new Date(y,m-1,d).toLocaleDateString("en-KE", {
        weekday:"long",day:"numeric",month:"long",year:"numeric"
    });
}
function showNotice(message, error=false) {
    notice.hidden = false;
    notice.className = "cc-notice" + (error ? " error" : "");
    notice.textContent = message;
}
function setSummary(items) {
    const count = status => items.filter(item => item.status === status).length;
    byId("paidCount").textContent = count("PAID");
    byId("unpaidCount").textContent = count("UNPAID");
    byId("upcomingCount").textContent = count("UPCOMING");
    byId("notDueCount").textContent = count("NOT_DUE");
    byId("reviewCount").textContent = count("START_DATE_REQUIRED");
    byId("startDateWarning").hidden = count("START_DATE_REQUIRED") === 0;
}
function renderDetails(item) {
    if (!item) {
        byId("selectedDateTitle").textContent = "Select a Thursday";
        byId("selectedDateIntro").textContent = "Choose a Thursday on the calendar.";
        byId("selectedStatus").textContent = "Not selected";
        byId("selectedStatus").className = "cc-status-pill";
        byId("selectedAmountDue").textContent = "-";
        byId("selectedAmountCovered").textContent = "-";
        byId("selectedAllocationCount").textContent = "-";
        byId("selectedExplanation").textContent = "Select a Thursday to review its status.";
        return;
    }
    const info = statusInfo[item.status] || statusInfo.START_DATE_REQUIRED;
    byId("selectedDateTitle").textContent = longDate(item.date);
    byId("selectedDateIntro").textContent = "Contribution record for " + item.date + ".";
    byId("selectedStatus").textContent = info.label;
    byId("selectedStatus").className = "cc-status-pill " + info.css;
    byId("selectedAmountDue").textContent = money.format(Number(item.amount_due) || 0);
    byId("selectedAmountCovered").textContent = money.format(Number(item.amount_covered) || 0);
    byId("selectedAllocationCount").textContent = String(item.allocation_count || 0);
    byId("selectedExplanation").textContent = info.note;
}
function render() {
    if (!loadedCalendar) return;

    const items = loadedCalendar.items || [];
    const index = new Map(items.map(item => [item.date,item]));
    byId("monthTitle").textContent = loadedCalendar.month_label;
    byId("monthSubtitle").textContent = "Each Thursday represents one weekly contribution period.";
    byId("weeklyRate").textContent = money.format(loadedCalendar.weekly_amount) + " / week";
    setSummary(items);
    grid.replaceChildren();

    const first = new Date(year,month-1,1);
    const days = new Date(year,month,0).getDate();
    const offset = (first.getDay()+6)%7;
    const now = new Date();
    const todayKey = dateKey(now.getFullYear(),now.getMonth()+1,now.getDate());

    for (let i=0;i<offset;i++) {
        const blank = node("div","cc-day cc-empty");
        blank.setAttribute("aria-hidden","true");
        grid.appendChild(blank);
    }

    for (let day=1;day<=days;day++) {
        const key = dateKey(year,month,day);
        const item = index.get(key);
        if (!item) {
            grid.appendChild(node("div","cc-day",undefined));
            grid.lastChild.appendChild(node("span","cc-day-number",day));
            continue;
        }

        const info = statusInfo[item.status] || statusInfo.START_DATE_REQUIRED;
        const classes = ["cc-day",info.css,key===selectedDate?"selected":"",key===todayKey?"today":""].filter(Boolean).join(" ");
        const button = node("button",classes);
        button.type = "button";
        button.setAttribute("aria-label",longDate(key)+": "+info.label);
        button.setAttribute("aria-pressed",key===selectedDate?"true":"false");
        button.appendChild(node("span","cc-day-number",day));
        button.appendChild(node("span","cc-badge",info.badge));
        button.addEventListener("click",()=>{
            selectedDate = key;
            render();
            renderDetails(item);
        });
        grid.appendChild(button);
    }

    const tail = (7-((offset+days)%7))%7;
    for (let i=0;i<tail;i++) {
        const blank=node("div","cc-day cc-empty");
        blank.setAttribute("aria-hidden","true");
        grid.appendChild(blank);
    }

    renderDetails(items.find(item=>item.date===selectedDate)||null);
}
async function load() {
    const thisRequest = ++requestId;
    showNotice("Loading your contribution calendar...");

    const query = new URLSearchParams({year:String(year),month:String(month)});
    try {
        const response = await fetch("/api/member/contribution-calendar?"+query.toString(), {
            method:"GET",
            credentials:"same-origin",
            headers:{"Accept":"application/json"},
            cache:"no-store"
        });
        let result;
        try { result = await response.json(); }
        catch (_) { throw new Error("The calendar server returned an unreadable response."); }

        if (thisRequest !== requestId) return;
        if (response.status===401) {
            window.location.assign("/login");
            return;
        }
        if (!response.ok || !result.success || !result.calendar) {
            throw new Error(result.message || "The calendar could not be loaded.");
        }

        loadedCalendar=result.calendar;
        byId("memberIdentity").textContent =
            result.member && result.member.name
                ? result.member.name+" | "+result.member.member_id
                : "Your TLC member account";

        const items=loadedCalendar.items||[];
        if (!items.some(item=>item.date===selectedDate)) {
            selectedDate=items.length?items[0].date:null;
        }
        render();
        workspace.hidden=false;
        notice.hidden=true;
    } catch (error) {
        if (thisRequest!==requestId) return;
        showNotice(error.message||"Unable to load the calendar. Please try again.",true);
    }
}
function changeMonth(amount) {
    const next = new Date(year,month-1+amount,1);
    year=next.getFullYear();
    month=next.getMonth()+1;
    selectedDate=null;
    load();
}

byId("previousMonth").addEventListener("click",()=>changeMonth(-1));
byId("nextMonth").addEventListener("click",()=>changeMonth(1));
byId("currentMonth").addEventListener("click",()=>{
    year=today.getFullYear();
    month=today.getMonth()+1;
    selectedDate=null;
    load();
});
load();
})();
