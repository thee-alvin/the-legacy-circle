from pathlib import Path
import re

path = Path(r"frontend\pages\tlc_analytics.html")

backup = Path(r"frontend\pages\tlc_analytics.before-live-cleanup.html")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

# Remove temporary alert testing from the button.
text = text.replace(
    'id="liveToggle" onclick="alert(\'TLC BUTTON CLICKED\')"',
    'id="liveToggle"'
)

text = text.replace(
    'id="liveToggle" onclick="alert(\'TLC BUTTON CLICKED\')" ',
    'id="liveToggle" '
)

# Remove the extra script block added during troubleshooting.
text = re.sub(
    r'\n<script>\s*document\.addEventListener\("DOMContentLoaded", function \(\) \{\s*const liveButton\s*=\s*document\.getElementById\("liveToggle"\);.*?\n</script>\s*</body>',
    '\n</body>',
    text,
    flags=re.S
)

# Add robust button binding before the first script closes.
binding = r'''
/* ============================================================
   LIVE MONITORING CONTROL
   ============================================================ */

function bindLiveMonitoringControl() {

    const liveButton =
        document.getElementById("liveToggle");

    if (!liveButton) {
        return;
    }

    liveButton.type = "button";

    liveButton.addEventListener(
        "click",
        function (event) {

            event.preventDefault();
            event.stopPropagation();

            toggleLiveMonitoring();
        }
    );

    updateLiveStatus();
}

if (document.readyState === "loading") {

    document.addEventListener(
        "DOMContentLoaded",
        bindLiveMonitoringControl
    );

} else {

    bindLiveMonitoringControl();
}
'''

# Add initial live scheduling after loadAnalytics() if it is not already initialized.
startup = r'''
loadAnalytics();

if (liveMonitoringEnabled) {
    scheduleLiveRefresh();
}
'''

if "function bindLiveMonitoringControl()" not in text:

    # Replace the existing standalone loadAnalytics(); call.
    text = text.replace(
        "loadAnalytics();\n\n\n// TLC-LIVE-MONITOR-JS",
        "loadAnalytics();\n\n\n// TLC-LIVE-MONITOR-JS"
    )

    # Put the binding immediately before the first closing script tag.
    first_script_end = text.find("</script>")

    if first_script_end != -1:
        text = (
            text[:first_script_end]
            + "\n"
            + binding
            + "\n"
            + text[first_script_end:]
        )

# Remove any duplicated live-control CSS patch and replace it with a clean rule.
text = re.sub(
    r'\n<style>\s*#liveToggle\s*\{.*?\}\s*</style>',
    '',
    text,
    flags=re.S
)

live_css = r'''
<style>
#liveToggle {
    position: relative;
    z-index: 10;
    pointer-events: auto;
    cursor: pointer;
}
</style>
'''

if "#liveToggle {" not in text:
    text = text.replace("</head>", live_css + "\n</head>")

path.write_text(text, encoding="utf-8")

print("Analytics live-monitoring cleanup completed.")
print(f"Backup: {backup}")
