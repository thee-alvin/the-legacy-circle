from pathlib import Path

path = Path(r"frontend/js/dashboard.js")
text = path.read_text(encoding="utf-8")

marker = "// DASHBOARD ANNOUNCEMENTS WILL BE ADDED HERE"

function = r'''
/* ============================================================
   DASHBOARD ANNOUNCEMENTS
   ============================================================ */

async function loadDashboardAnnouncements() {

    const list = document.getElementById("announcementList");

    if (!list) {
        return;
    }

    try {

        const response = await fetch(
            "/api/member/announcements",
            {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json"
                },
                cache: "no-store"
            }
        );

        const data = await response.json();

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok || !data.success) {
            return;
        }

        const announcements = Array.isArray(data.announcements)
            ? data.announcements
            : [];

        if (!announcements.length) {
            return;
        }

        list.innerHTML = announcements
            .slice(0, 3)
            .map((announcement) => {

                const title = String(
                    announcement.title ||
                    announcement.Title ||
                    "TLC Announcement"
                ).trim();

                const message = String(
                    announcement.message ||
                    announcement.Message ||
                    ""
                ).trim();

                const rawDate =
                    announcement.announcement_date ||
                    announcement.AnnouncementDate ||
                    announcement.date ||
                    "";

                let formattedDate = "";

                if (rawDate) {
                    const date = new Date(rawDate);

                    if (!Number.isNaN(date.getTime())) {
                        formattedDate = date.toLocaleDateString(
                            "en-KE",
                            {
                                day: "numeric",
                                month: "short",
                                year: "numeric"
                            }
                        );
                    }
                }

                const shortMessage =
                    message.length > 110
                        ? message.substring(0, 110) + "..."
                        : message;

                return `
                    <div class="dashboard-announcement-item">

                        <div class="dashboard-announcement-icon">
                            📢
                        </div>

                        <div class="dashboard-announcement-content">

                            <strong>${title}</strong>

                            ${
                                shortMessage
                                    ? `<p>${shortMessage}</p>`
                                    : ""
                            }

                            ${
                                formattedDate
                                    ? `<small>${formattedDate}</small>`
                                    : ""
                            }

                        </div>

                    </div>
                `;
            })
            .join("");

    } catch (error) {

        console.error(
            "Dashboard announcements:",
            error
        );
    }
}

document.addEventListener(
    "DOMContentLoaded",
    loadDashboardAnnouncements
);
'''

if "async function loadDashboardAnnouncements" not in text:
    text = text.replace(marker, function)
    path.write_text(text, encoding="utf-8")
    print("Dashboard announcements added successfully.")
else:
    print("Dashboard announcements already exist.")
