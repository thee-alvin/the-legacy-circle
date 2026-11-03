

function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function formatTime(value) {

    if (!value) {
        return "—";
    }

    try {

        return new Date(value)
            .toLocaleString(
                undefined,
                {
                    dateStyle: "medium",
                    timeStyle: "short"
                }
            );

    } catch {

        return value;
    }
}


function populateMembers(members) {

    const select =
        document.getElementById(
            "memberFilter"
        );

    const current =
        select.value;

    select.innerHTML =
        '<option value="">All Members</option>';

    members.forEach(
        member => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                member.member_id;

            option.textContent =
                `${member.name} (${member.member_id})`;

            select.appendChild(option);
        }
    );

    select.value = current;
}


function populateSelect(
    elementId,
    values,
    label
) {

    const select =
        document.getElementById(
            elementId
        );

    const current =
        select.value;

    select.innerHTML =
        `<option value="">${label}</option>`;

    values.forEach(
        value => {

            const option =
                document.createElement(
                    "option"
                );

            option.value = value;
            option.textContent = value;

            select.appendChild(
                option
            );
        }
    );

    select.value = current;
}


function applyFilters() {
    loadAnalytics();
}


async function resetAnalytics() {

    try {

        const response = await fetch(
            "/api/tlc/analytics/reset",
            {
                method: "POST",
                credentials: "same-origin"
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {

            alert(
                data.message ||
                "Unable to reset analytics."
            );

            return;
        }

        await loadAnalytics();

    } catch (error) {

        console.error(error);

        alert(
            "Unable to reset analytics."
        );
    }
}


function renderDailyChart(
    elementId,
    series,
    valueKey,
    loginMode
) {

    const element =
        document.getElementById(
            elementId
        );

    if (!element) {
        return;
    }

    element.innerHTML = "";

    if (!Array.isArray(series) || !series.length) {

        element.innerHTML =
            '<div class="chart-empty">No chart data available.</div>';

        return;
    }

    const values = series.map(
        item =>
            Number(
                item[valueKey] || 0
            )
    );

    const maximum = Math.max(
        1,
        ...values
    );

    series.forEach(
        (item, index) => {

            const value = Number(
                item[valueKey] || 0
            );

            const column =
                document.createElement(
                    "div"
                );

            column.className =
                "daily-column";

            const bar =
                document.createElement(
                    "div"
                );

            bar.className =
                loginMode
                    ? "daily-bar login"
                    : "daily-bar";

            const percentage =
                value > 0
                    ? (value / maximum) * 100
                    : 1.5;

            bar.style.height =
                `${percentage}%`;

            bar.title =
                `${item.date}: ${value}`;

            const label =
                document.createElement(
                    "div"
                );

            label.className =
                "daily-label";

            label.textContent =
                String(
                    item.date || ""
                ).slice(5);

            column.appendChild(
                bar
            );

            column.appendChild(
                label
            );

            element.appendChild(
                column
            );
        }
    );
}

function renderMetricBars(
    elementId,
    data
) {

    const element =
        document.getElementById(
            elementId
        );

    if (!element) {
        return;
    }

    element.innerHTML = "";

    const entries =
        Object.entries(
            data || {}
        ).sort(
            (a, b) =>
                Number(b[1])
                - Number(a[1])
        );

    if (entries.length === 0) {

        element.innerHTML =
            '<div class="chart-empty">No chart data available.</div>';

        return;
    }

    const maximum =
        Math.max(
            1,
            ...entries.map(
                entry =>
                    Number(entry[1])
            )
        );

    entries.forEach(
        ([name, value]) => {

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "metric-row";

            const label =
                document.createElement(
                    "div"
                );

            label.className =
                "metric-name";

            label.textContent =
                name;

            label.title =
                name;

            const track =
                document.createElement(
                    "div"
                );

            track.className =
                "metric-track";

            const fill =
                document.createElement(
                    "div"
                );

            fill.className =
                "metric-fill";

            fill.style.width =
                `${(
                    Number(value)
                    / maximum
                ) * 100}%`;

            const count =
                document.createElement(
                    "div"
                );

            count.className =
                "metric-count";

            count.textContent =
                value;

            track.appendChild(
                fill
            );

            row.appendChild(
                label
            );

            row.appendChild(
                track
            );

            row.appendChild(
                count
            );

            element.appendChild(
                row
            );
        }
    );
}


async function loadAnalyticsNow() {

    try {

        const params =
            new URLSearchParams();

        const member =
            document.getElementById(
                "memberFilter"
            ).value;

        const action =
            document.getElementById(
                "actionFilter"
            ).value;

        const category =
            document.getElementById(
                "categoryFilter"
            ).value;

        const dateFrom =
            document.getElementById(
                "dateFrom"
            ).value;

        const dateTo =
            document.getElementById(
                "dateTo"
            ).value;

        if (member) {
            params.set(
                "member_id",
                member
            );
        }

        if (action) {
            params.set(
                "action",
                action
            );
        }

        if (category) {
            params.set(
                "category",
                category
            );
        }

        if (dateFrom) {
            params.set(
                "date_from",
                dateFrom
            );
        }

        if (dateTo) {
            params.set(
                "date_to",
                dateTo
            );
        }

        const response =
            await fetch(
                `/api/tlc/analytics?${params.toString()}`,
                {
                    credentials:
                        "same-origin"
                }
            );

        const data =
            await response.json();

        if (
            !response.ok
            || !data.success
        ) {

            alert(
                data.message ||
                "Unable to load analytics."
            );

            return;
        }


        document.getElementById(
            "totalMembers"
        ).textContent =
            data.summary.total_members;

        document.getElementById(
            "totalActivities"
        ).textContent =
            data.summary.total_activities;

        document.getElementById(
            "totalLogins"
        ).textContent =
            data.summary.total_logins;

        document.getElementById(
            "todayLogins"
        ).textContent =
            data.summary.today_logins;

        document.getElementById(
            "uniqueMembers"
        ).textContent =
            data.summary.unique_members;


        const activeMember =
            data.summary.most_active_member;

        document.getElementById(
            "mostActiveMember"
        ).textContent =
            activeMember
                ? activeMember.name
                : "-";

        document.getElementById(
            "mostActiveCount"
        ).textContent =
            activeMember
                ? `${activeMember.activities} activities`
                : "0 activities";


        const peakDay =
            data.summary.peak_activity_day;

        document.getElementById(
            "peakActivityDay"
        ).textContent =
            peakDay
                ? peakDay.date
                : "-";

        document.getElementById(
            "peakActivityCount"
        ).textContent =
            peakDay
                ? `${peakDay.activities} activities`
                : "0 activities";


        const latest =
            data.summary.latest_activity;

        document.getElementById(
            "latestActivity"
        ).textContent =
            latest
                ? (
                    latest.action
                    || "Activity"
                )
                : "-";

        document.getElementById(
            "latestActivityTime"
        ).textContent =
            latest
                ? formatTime(
                    latest.timestamp
                )
                : "No activity";


        document.getElementById(
            "loginEvents"
        ).textContent =
            data.summary.login_events || 0;



        populateMembers(
            data.members || []
        );


        populateSelect(
            "actionFilter",
            Object.keys(
                data.actions || {}
            ).sort(),
            "All Actions"
        );


        populateSelect(
            "categoryFilter",
            Object.keys(
                data.categories || {}
            ).sort(),
            "All Categories"
        );


        const memberSummary =
            document.getElementById(
                "memberSummary"
            );


        if (data.member) {

            memberSummary.style.display =
                "grid";

            document.getElementById(
                "memberName"
            ).textContent =
                data.member.name;

            document.getElementById(
                "memberId"
            ).textContent =
                data.member.member_id;

            document.getElementById(
                "lastLogin"
            ).textContent =
                formatTime(
                    data.summary.member_last_login
                );

            document.getElementById(
                "memberActivities"
            ).textContent =
                data.summary.total_activities;

        } else {

            memberSummary.style.display =
                "none";
        }



        renderDailyChart(
            "activityTrendChart",
            data.daily_series || [],
            "activities",
            false
        );

        renderDailyChart(
            "loginTrendChart",
            data.daily_series || [],
            "logins",
            true
        );

        renderMetricBars(
            "categoryBarsChart",
            data.categories || {}
        );

        renderMetricBars(
            "actionBarsChart",
            data.actions || {}
        );

        renderSummary(
            "categorySummary",
            data.categories || {}
        );

        renderSummary(
            "actionSummary",
            data.actions || {}
        );


        const body =
            document.getElementById(
                "activityBody"
            );

        body.innerHTML = "";


        if (
            !data.activities
            || data.activities.length === 0
        ) {

            body.innerHTML =
                '<tr><td colspan="5" class="muted">No activity found for the selected filters.</td></tr>';

            return;
        }


        data.activities.forEach(
            activity => {

                const row =
                    document.createElement(
                        "tr"
                    );

                row.innerHTML = `
                    <td>${escapeHtml(activity.member_id || "")}</td>
                    <td>${escapeHtml(activity.action || "")}</td>
                    <td>${escapeHtml(activity.category || "")}</td>
                    <td>${escapeHtml(activity.description || "")}</td>
                    <td>${escapeHtml(formatTime(activity.timestamp))}</td>
                `;

                body.appendChild(row);
            }
        );

    } catch (error) {

        console.error(error);

        alert(
            "Unable to load TLC analytics."
        );
    }
}


function renderSummary(
    elementId,
    values
) {

    const element =
        document.getElementById(
            elementId
        );

    element.innerHTML = "";

    const entries =
        Object.entries(values)
            .sort(
                (a, b) =>
                    b[1] - a[1]
            );

    if (
        entries.length === 0
    ) {

        element.innerHTML =
            '<li class="muted">No data</li>';

        return;
    }

    entries.forEach(
        ([name, count]) => {

            const li =
                document.createElement(
                    "li"
                );

            li.innerHTML = `
                <span>${escapeHtml(name)}</span>
                <strong>${count}</strong>
            `;

            element.appendChild(
                li
            );
        }
    );
}


loadAnalytics();


// TLC-LIVE-MONITOR-JS

let liveMonitoringEnabled = true;
let liveRefreshTimer = null;
let firstLiveLoad = true;
let lastActivitySignature = null;

function getLatestActivitySignature(data) {

    if (
        !data
        || !Array.isArray(data.activities)
        || data.activities.length === 0
    ) {
        return null;
    }

    const latest = data.activities[0];

    return String(
        latest.id
        || (
            String(latest.member_id || "")
            + "|"
            + String(latest.action || "")
            + "|"
            + String(latest.timestamp || "")
        )
    );
}


function showLiveNotice(activity) {

    const notice =
        document.getElementById(
            "liveActivityNotice"
        );

    if (!notice || !activity) {
        return;
    }

    notice.innerHTML = `
        <strong>New TLC activity detected</strong>
        <span>
            ${escapeHtml(activity.member_id || "")}
            - ${escapeHtml(activity.action || "Activity")}
        </span>
    `;

    notice.style.display = "block";

    window.clearTimeout(
        showLiveNotice.timer
    );

    showLiveNotice.timer =
        window.setTimeout(
            () => {
                notice.style.display = "none";
            },
            5000
        );
}


function updateLiveStatus() {

    const dot =
        document.getElementById(
            "liveDot"
        );

    const state =
        document.getElementById(
            "liveState"
        );

    const button =
        document.getElementById(
            "liveToggle"
        );

    if (!dot || !state || !button) {
        return;
    }

    if (liveMonitoringEnabled) {

        dot.classList.remove(
            "paused"
        );

        state.textContent =
            "Live monitoring ON";

        button.textContent =
            "Pause Live";

    } else {

        dot.classList.add(
            "paused"
        );

        state.textContent =
            "Live monitoring PAUSED";

        button.textContent =
            "Resume Live";
    }
}


function toggleLiveMonitoring() {

    liveMonitoringEnabled = !liveMonitoringEnabled;

    if (!liveMonitoringEnabled) {

        window.clearTimeout(liveRefreshTimer);
        liveRefreshTimer = null;

        updateLiveStatus();
        return;
    }

    updateLiveStatus();
    scheduleLiveRefresh();
}


function scheduleLiveRefresh() {

    window.clearTimeout(liveRefreshTimer);
    liveRefreshTimer = null;

    if (!liveMonitoringEnabled) {
        return;
    }

    liveRefreshTimer = window.setTimeout(
        async () => {

            if (!liveMonitoringEnabled) {
                liveRefreshTimer = null;
                return;
            }

            await refreshLiveAnalytics();

            if (liveMonitoringEnabled) {
                scheduleLiveRefresh();
            } else {
                liveRefreshTimer = null;
            }

        },
        10000
    );
}


async function refreshLiveAnalytics() {

    try {

        const previousSignature =
            lastActivitySignature;

        await loadAnalyticsNow();

        const response =
            await fetch(
                buildAnalyticsUrl(),
                {
                    credentials:
                        "same-origin"
                }
            );

        const data =
            await response.json();

        if (
            !response.ok
            || !data.success
        ) {
            return;
        }

        const currentSignature =
            getLatestActivitySignature(
                data
            );

        if (
            !firstLiveLoad
            && currentSignature
            && previousSignature
            && currentSignature !== previousSignature
            && data.activities
            && data.activities.length
        ) {

            showLiveNotice(
                data.activities[0]
            );
        }

        lastActivitySignature =
            currentSignature;

        firstLiveLoad = false;

        const updated =
            document.getElementById(
                "analyticsUpdated"
            );

        if (updated) {

            updated.textContent =
                new Date().toLocaleTimeString();
        }

    } catch (error) {

        console.error(
            "TLC live analytics refresh failed:",
            error
        );
    }
}


function buildAnalyticsUrl() {

    const params =
        new URLSearchParams();

    const member =
        document.getElementById(
            "memberFilter"
        )?.value || "";

    const action =
        document.getElementById(
            "actionFilter"
        )?.value || "";

    const category =
        document.getElementById(
            "categoryFilter"
        )?.value || "";

    const dateFrom =
        document.getElementById(
            "dateFrom"
        )?.value || "";

    const dateTo =
        document.getElementById(
            "dateTo"
        )?.value || "";

    if (member) {
        params.set(
            "member_id",
            member
        );
    }

    if (action) {
        params.set(
            "action",
            action
        );
    }

    if (category) {
        params.set(
            "category",
            category
        );
    }

    if (dateFrom) {
        params.set(
            "date_from",
            dateFrom
        );
    }

    if (dateTo) {
        params.set(
            "date_to",
            dateTo
        );
    }

    return (
        "/api/tlc/analytics?"
        + params.toString()
    );
}





document.addEventListener("DOMContentLoaded", function () {

    const liveButton =
        document.getElementById("liveToggle");

    if (!liveButton) {
        return;
    }

    liveButton.onclick = function (event) {

        event.preventDefault();
        event.stopPropagation();

        toggleLiveMonitoring();
    };

    updateLiveStatus();
});
