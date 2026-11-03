from pathlib import Path

# ============================================================
# 1. FIX + RUN THE EXCEL ANNOUNCEMENT SCRIPT
# ============================================================

announcement_script = Path(
    r".\scripts\add_october_welcome_announcement.py"
)

script_text = announcement_script.read_text(
    encoding="utf-8-sig"
)

if "from copy import copy" not in script_text:
    script_text = script_text.replace(
        "from datetime import datetime, date",
        "from datetime import datetime, date\nfrom copy import copy",
        1
    )

announcement_script.write_text(
    script_text,
    encoding="utf-8"
)

print("")
print("Running announcement workbook update...")
print("")

# Execute the existing announcement script.
exec(
    compile(
        script_text,
        str(announcement_script),
        "exec"
    ),
    {
        "__name__": "__main__",
        "__file__": str(announcement_script)
    }
)

# ============================================================
# 2. ANNOUNCEMENT PAGE JAVASCRIPT
# ============================================================

js = Path(
    r".\frontend\js\announcements.js"
)

js_text = js.read_text(
    encoding="utf-8-sig"
)

if "tlc-october-poster" not in js_text:

    poster_function = r'''

/* ============================================================
   OCTOBER 2026 WELCOME POSTER
   Rendered entirely in HTML/CSS — no image file required.
   ============================================================ */

function enhanceOctoberWelcomeAnnouncement() {

    const list = document.getElementById(
        "announcementsList"
    );

    if (!list) {
        return;
    }

    const cards = list.querySelectorAll(
        ".announcement-card"
    );

    cards.forEach((card) => {

        const titleElement = card.querySelector(
            ".announcement-title"
        );

        const title = (
            titleElement?.textContent || ""
        ).trim().toUpperCase();

        if (
            title !== "WELCOME TO OCTOBER 2026"
            || card.querySelector(".tlc-october-poster")
        ) {
            return;
        }

        const poster = document.createElement("div");

        poster.className = "tlc-october-poster";

        poster.innerHTML = `
            <div class="tlc-october-poster-glow"></div>

            <div class="tlc-october-poster-top">
                <span class="tlc-october-poster-mark">
                    TLC
                </span>

                <span class="tlc-october-poster-label">
                    THE LEGACY CIRCLE
                </span>
            </div>

            <div class="tlc-october-poster-main">

                <span class="tlc-october-poster-kicker">
                    WELCOME TO A NEW MONTH
                </span>

                <div class="tlc-october-number">
                    10
                </div>

                <div class="tlc-october-month">
                    OCTOBER
                </div>

                <div class="tlc-october-year">
                    2026
                </div>

                <div class="tlc-october-divider"></div>

                <p>
                    United in Purpose.<br>
                    Built to Last.
                </p>

            </div>

            <div class="tlc-october-poster-footer">
                <span>
                    THE LEGACY CIRCLE TREASURY
                </span>

                <span>
                    OCTOBER 2026
                </span>
            </div>
        `;

        card.insertBefore(
            poster,
            card.firstChild
        );
    });
}


/*
 * The announcement data is loaded asynchronously from Excel.
 * Observe the announcement list so the poster is inserted as
 * soon as the announcement cards arrive.
 */

const octoberPosterObserver = new MutationObserver(
    enhanceOctoberWelcomeAnnouncement
);

const octoberPosterList =
    document.getElementById(
        "announcementsList"
    );

if (octoberPosterList) {

    octoberPosterObserver.observe(
        octoberPosterList,
        {
            childList: true,
            subtree: true
        }
    );

    enhanceOctoberWelcomeAnnouncement();
}

'''

    js_text += poster_function

    js.write_text(
        js_text,
        encoding="utf-8"
    )

    print(
        "October poster renderer added to announcements.js"
    )

else:

    print(
        "October poster renderer already exists."
    )


# ============================================================
# 3. ANNOUNCEMENT PAGE CSS
# ============================================================

css = Path(
    r".\frontend\assets\announcements.css"
)

css_text = css.read_text(
    encoding="utf-8-sig"
)

if "tlc-october-poster" not in css_text:

    poster_css = r'''

/* ============================================================
   TLC OCTOBER 2026 CODED ANNOUNCEMENT POSTER
   ============================================================ */

.tlc-october-poster {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    min-height: 360px;
    margin: 0 0 24px;
    padding: 26px;
    border-radius: 24px;
    color: #fff;
    background:
        radial-gradient(
            circle at 85% 15%,
            rgba(201, 164, 74, .30),
            transparent 26%
        ),
        radial-gradient(
            circle at 12% 85%,
            rgba(54, 113, 151, .28),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #091523 0%,
            #11283e 52%,
            #182f48 100%
        );
    box-shadow:
        0 18px 45px rgba(4, 14, 25, .20),
        inset 0 0 0 1px rgba(255,255,255,.08);
}

.tlc-october-poster::before,
.tlc-october-poster::after {
    content: "";
    position: absolute;
    z-index: -1;
    border-radius: 50%;
    pointer-events: none;
}

.tlc-october-poster::before {
    width: 230px;
    height: 230px;
    right: -90px;
    top: -95px;
    border: 1px solid rgba(214, 179, 91, .28);
    box-shadow:
        0 0 0 20px rgba(214,179,91,.035),
        0 0 0 40px rgba(214,179,91,.025);
}

.tlc-october-poster::after {
    width: 170px;
    height: 170px;
    left: -80px;
    bottom: -100px;
    border: 1px solid rgba(255,255,255,.09);
}

.tlc-october-poster-glow {
    position: absolute;
    z-index: -1;
    width: 320px;
    height: 320px;
    left: 50%;
    top: 42%;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: rgba(214,179,91,.06);
    filter: blur(2px);
}

.tlc-october-poster-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding-bottom: 18px;
    border-bottom: 1px solid rgba(255,255,255,.11);
}

.tlc-october-poster-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    border-radius: 14px;
    font-size: 14px;
    font-weight: 900;
    letter-spacing: .08em;
    color: #111b29;
    background: linear-gradient(
        135deg,
        #f0d27a,
        #caa451
    );
    box-shadow:
        0 8px 18px rgba(0,0,0,.16);
}

.tlc-october-poster-label {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: rgba(255,255,255,.78);
}

.tlc-october-poster-main {
    position: relative;
    text-align: center;
    padding: 34px 12px 30px;
}

.tlc-october-poster-kicker {
    display: block;
    margin-bottom: 8px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .20em;
    text-transform: uppercase;
    color: #e4c56e;
}

.tlc-october-number {
    margin-top: -4px;
    font-size: clamp(74px, 11vw, 128px);
    line-height: .82;
    font-weight: 950;
    letter-spacing: -.08em;
    color: rgba(255,255,255,.07);
    user-select: none;
}

.tlc-october-month {
    margin-top: -58px;
    font-size: clamp(34px, 6vw, 64px);
    line-height: 1;
    font-weight: 950;
    letter-spacing: .08em;
    color: #fff;
}

.tlc-october-year {
    margin-top: 7px;
    font-size: 17px;
    font-weight: 800;
    letter-spacing: .32em;
    text-indent: .32em;
    color: #d9b85e;
}

.tlc-october-divider {
    width: 76px;
    height: 2px;
    margin: 22px auto 17px;
    border-radius: 999px;
    background: linear-gradient(
        90deg,
        transparent,
        #d8b75c,
        transparent
    );
}

.tlc-october-poster-main p {
    margin: 0;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 17px;
    line-height: 1.55;
    font-style: italic;
    color: rgba(255,255,255,.92);
}

.tlc-october-poster-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding-top: 17px;
    border-top: 1px solid rgba(255,255,255,.11);
}

.tlc-october-poster-footer span {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: .11em;
    text-transform: uppercase;
    color: rgba(255,255,255,.66);
}

.tlc-october-poster-footer span:last-child {
    color: #dfbd64;
}

.announcement-card:has(
    .tlc-october-poster
) {
    padding-top: 0;
}

@media (max-width: 640px) {

    .tlc-october-poster {
        min-height: 330px;
        padding: 19px;
        border-radius: 19px;
    }

    .tlc-october-poster-top {
        align-items: flex-start;
    }

    .tlc-october-poster-label {
        max-width: 190px;
        text-align: right;
        line-height: 1.5;
    }

    .tlc-october-poster-footer {
        flex-direction: column;
        align-items: flex-start;
    }

    .tlc-october-month {
        margin-top: -46px;
    }
}
'''

    css_text += poster_css

    css.write_text(
        css_text,
        encoding="utf-8"
    )

    print(
        "October poster styles added to announcements.css"
    )

else:

    print(
        "October poster styles already exist."
    )

print("")
print("================================================")
print("OCTOBER ANNOUNCEMENT + CODED POSTER READY")
print("================================================")
