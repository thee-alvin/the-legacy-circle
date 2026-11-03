(() => {
    "use strict";

    const directory = document.getElementById("officialsGrid");
    const officeStatus = document.getElementById("officeStatus");
    const positionCount = document.getElementById("positionCount");
    const dialog = document.getElementById("officialEditor");
    const form = document.getElementById("officialForm");
    const editorMessage = document.getElementById("editorMessage");
    const editorPosition = document.getElementById("editorPosition");
    const saveButton = document.getElementById("saveOfficial");

    let currentState = {
        officials: [],
        can_manage: false
    };

    let editedKey = null;

    const fields = {
        name: document.getElementById("officialName"),
        member_id: document.getElementById("officialMemberId"),
        email: document.getElementById("officialEmail"),
        contact: document.getElementById("officialContact"),
        photo_url: document.getElementById("officialPhoto"),
        term_start: document.getElementById("termStart"),
        term_end: document.getElementById("termEnd"),
        status: document.getElementById("officialStatus"),
        biography: document.getElementById("officialBiography")
    };

    function setOfficeStatus(message, isError = false) {
        officeStatus.textContent = message || "";
        officeStatus.classList.toggle("is-error", Boolean(isError));
    }

    function element(tag, className, text) {
        const node = document.createElement(tag);

        if (className) {
            node.className = className;
        }

        if (text !== undefined && text !== null) {
            node.textContent = String(text);
        }

        return node;
    }

    function initials(name) {
        const words = String(name || "").trim().split(/\s+/).filter(Boolean);

        if (!words.length) {
            return "TLC";
        }

        return words.slice(0, 2).map(word => word.charAt(0).toUpperCase()).join("");
    }

    function dateLabel(value) {
        if (!value) {
            return "";
        }

        const date = new Date(`${value}T00:00:00`);

        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return date.toLocaleDateString(undefined, {
            day: "numeric",
            month: "short",
            year: "numeric"
        });
    }

    function statusLabel(value) {
        if (value === "ACTIVE") {
            return "ACTIVE OFFICIAL";
        }

        if (value === "FORMER") {
            return "FORMER OFFICIAL";
        }

        return "POSITION VACANT";
    }


    function createOfficialCard(official) {
        const card = element("article", "official-card");
        card.dataset.position = official.key || "";

        const banner = element("div", "official-card-banner");

        const fallbackMarks = {
            CHAIRPERSON: "CH",
            VICE_CHAIRPERSON: "VC",
            SECRETARY: "SE",
            TREASURER: "TR"
        };

        const avatarText = official.name
            ? initials(official.name)
            : (fallbackMarks[official.key] || "TLC");

        const avatar = element("div", "official-avatar", avatarText);
        avatar.setAttribute("aria-hidden", "true");

        if (official.photo_url && official.name) {
            const image = document.createElement("img");

            image.src = official.photo_url;
            image.alt = `${official.name} profile photograph`;
            image.loading = "lazy";
            image.decoding = "async";

            image.addEventListener("error", () => {
                image.remove();
                avatar.textContent = avatarText;
            });

            avatar.appendChild(image);
        }

        const badgeClass = official.status === "VACANT"
            ? "official-status status-vacant"
            : official.status === "FORMER"
                ? "official-status status-former"
                : "official-status";

        const badge = element(
            "span",
            badgeClass,
            statusLabel(official.status)
        );

        banner.append(avatar, badge);
        card.appendChild(banner);

        const body = element("div", "official-card-body");

        body.appendChild(
            element("p", "official-position", official.position)
        );

        const officialName = official.name || (
            official.status === "FORMER"
                ? "Former Office Holder"
                : "Position Vacant"
        );

        body.appendChild(
            element("h2", "official-name", officialName)
        );

        if (official.member_id && official.name) {
            body.appendChild(
                element(
                    "p",
                    "official-member-id",
                    `Member ID: ${official.member_id}`
                )
            );
        }

        if (official.biography && official.name) {
            body.appendChild(
                element(
                    "p",
                    "official-profile-label",
                    "PROFILE AND RESPONSIBILITIES"
                )
            );

            body.appendChild(
                element(
                    "p",
                    "official-biography",
                    official.biography
                )
            );
        } else if (official.status === "VACANT") {
            body.appendChild(
                element(
                    "p",
                    "official-biography",
                    "This position is awaiting an official appointment."
                )
            );
        }

        if (official.status !== "VACANT") {
            const termSection = element("div", "official-term-section");

            termSection.appendChild(
                element("span", "official-term-label", "TERM OF OFFICE")
            );

            const termText = [];

            if (official.term_start) {
                termText.push(`From ${dateLabel(official.term_start)}`);
            }

            if (official.term_end) {
                termText.push(`Until ${dateLabel(official.term_end)}`);
            }

            if (termText.length === 0) {
                termText.push("Term dates not recorded");
            }

            termSection.appendChild(
                element(
                    "p",
                    "official-term",
                    termText.join(" | ")
                )
            );

            body.appendChild(termSection);
        }

        const footer = element("div", "official-card-footer");

        const viewButton = element(
            "button",
            "view-official-card-button",
            "View official card"
        );

        viewButton.type = "button";
        viewButton.dataset.viewKey = official.key;

        viewButton.setAttribute(
            "aria-label",
            `View official card for ${official.position}`
        );

        footer.appendChild(viewButton);

        if (currentState.can_manage) {
            const editButton = element(
                "button",
                "edit-official-button",
                "Edit official"
            );

            editButton.type = "button";
            editButton.dataset.editKey = official.key;

            editButton.setAttribute(
                "aria-label",
                `Edit ${official.position} details`
            );

            footer.appendChild(editButton);
        }

        body.appendChild(footer);

        card.appendChild(body);

        return card;
    }

    function renderDirectory() {
        directory.replaceChildren();

        const officials = Array.isArray(currentState.officials)
            ? currentState.officials
            : [];

        positionCount.textContent = String(officials.length).padStart(2, "0");

        for (const official of officials) {
            directory.appendChild(createOfficialCard(official));
        }

        if (currentState.can_manage) {
            setOfficeStatus(
                "Management access is enabled for your authorized TLC account. "
                + "Use Edit official to update an office holder or mark a position vacant."
            );
        } else {
            setOfficeStatus(
                "You are viewing the official TLC leadership directory. "
                + "Official records can only be changed by authorized administration."
            );
        }
    }

    async function loadDirectory() {
        setOfficeStatus("Loading the TLC leadership directory?");

        try {
            const response = await fetch("/api/member/presidency", {
                method: "GET",
                credentials: "same-origin",
                headers: { "Accept": "application/json" }
            });

            if (response.status === 401) {
                window.location.assign("/login");
                return;
            }

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(
                    result.message || "The leadership directory could not be loaded."
                );
            }

            currentState = result;
            renderDirectory();
        } catch (error) {
            directory.replaceChildren();
            setOfficeStatus(
                error.message || "Unable to load the officials directory. Please try again.",
                true
            );
        }
    }

    function openEditor(official) {
        if (!currentState.can_manage || !official) {
            return;
        }

        editedKey = official.key;
        form.reset();
        editorMessage.textContent = "";

        editorPosition.textContent = official.position;

        for (const [key, input] of Object.entries(fields)) {
            input.value = official[key] || "";
        }

        if (typeof dialog.showModal === "function") {
            dialog.showModal();
        } else {
            dialog.setAttribute("open", "");
        }

        fields.name.focus();
    }

    function closeEditor() {
        if (typeof dialog.close === "function" && dialog.open) {
            dialog.close();
        } else {
            dialog.removeAttribute("open");
        }

        editedKey = null;
    }


    // --------------------------------------------------------
    // OFFICIAL CARD PREVIEW AND PNG EXPORT
    // --------------------------------------------------------

    const officialCardDialog = document.getElementById("officialCardDialog");
    const officialCardCanvas = document.getElementById("officialCardCanvas");
    const cardDownloadStatus = document.getElementById("cardDownloadStatus");
    const downloadOfficialCard = document.getElementById("downloadOfficialCard");
    const cardDialogTitle = document.getElementById("cardDialogTitle");

    let currentCardOfficial = null;
    let cardRenderVersion = 0;

    function roundedPath(ctx, x, y, width, height, radius) {
        const r = Math.min(radius, width / 2, height / 2);

        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + width - r, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + r);
        ctx.lineTo(x + width, y + height - r);
        ctx.quadraticCurveTo(
            x + width,
            y + height,
            x + width - r,
            y + height
        );
        ctx.lineTo(x + r, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
    }

    function drawRoundRect(ctx, x, y, width, height, radius, fill, stroke) {
        roundedPath(ctx, x, y, width, height, radius);

        if (fill) {
            ctx.fillStyle = fill;
            ctx.fill();
        }

        if (stroke) {
            ctx.strokeStyle = stroke;
            ctx.stroke();
        }
    }

    function loadCardImage(source) {
        if (!source) {
            return Promise.resolve(null);
        }

        return new Promise(resolve => {
            let imageUrl;

            try {
                imageUrl = new URL(source, window.location.href);

                if (!["http:", "https:"].includes(imageUrl.protocol)) {
                    resolve(null);
                    return;
                }
            } catch {
                resolve(null);
                return;
            }

            const image = new Image();

            // Cross-origin photos must explicitly permit canvas use.
            // If they do not, use the initials fallback so PNG export
            // is still possible without a tainted canvas.
            if (imageUrl.origin !== window.location.origin) {
                image.crossOrigin = "anonymous";
            }

            image.onload = () => resolve(image);
            image.onerror = () => resolve(null);
            image.src = imageUrl.href;
        });
    }

    function drawImageContained(ctx, image, x, y, boxWidth, boxHeight) {
        if (!image || !image.naturalWidth || !image.naturalHeight) {
            return false;
        }

        const scale = Math.min(
            boxWidth / image.naturalWidth,
            boxHeight / image.naturalHeight
        );

        const width = image.naturalWidth * scale;
        const height = image.naturalHeight * scale;

        ctx.drawImage(
            image,
            x + (boxWidth - width) / 2,
            y + (boxHeight - height) / 2,
            width,
            height
        );

        return true;
    }

    function drawImageCover(ctx, image, x, y, width, height) {
        if (!image || !image.naturalWidth || !image.naturalHeight) {
            return false;
        }

        const scale = Math.max(
            width / image.naturalWidth,
            height / image.naturalHeight
        );

        const sourceWidth = width / scale;
        const sourceHeight = height / scale;
        const sourceX = (image.naturalWidth - sourceWidth) / 2;
        const sourceY = (image.naturalHeight - sourceHeight) / 2;

        ctx.drawImage(
            image,
            sourceX,
            sourceY,
            sourceWidth,
            sourceHeight,
            x,
            y,
            width,
            height
        );

        return true;
    }

    function wrapCardText(ctx, text, maxWidth, maxLines) {
        const words = String(text || "").trim().split(/\s+/).filter(Boolean);
        const lines = [];
        let current = "";

        for (const word of words) {
            const candidate = current ? `${current} ${word}` : word;

            if (current && ctx.measureText(candidate).width > maxWidth) {
                lines.push(current);
                current = word;
            } else {
                current = candidate;
            }
        }

        if (current) {
            lines.push(current);
        }

        if (lines.length > maxLines) {
            const shortened = lines.slice(0, maxLines);
            let last = shortened[maxLines - 1];

            while (
                last.length > 3 &&
                ctx.measureText(`${last}...`).width > maxWidth
            ) {
                last = last.slice(0, -1).trimEnd();
            }

            shortened[maxLines - 1] = `${last}...`;
            return shortened;
        }

        return lines;
    }

    function drawWrappedCardText(
        ctx,
        text,
        x,
        y,
        maxWidth,
        lineHeight,
        maxLines,
        align = "left"
    ) {
        const lines = wrapCardText(ctx, text, maxWidth, maxLines);

        ctx.textAlign = align;

        lines.forEach((line, index) => {
            ctx.fillText(line, x, y + index * lineHeight);
        });

        return lines.length;
    }

    function fitCardText(ctx, text, maxWidth, initialSize, minimumSize) {
        let size = initialSize;

        while (size > minimumSize) {
            ctx.font = `800 ${size}px "Segoe UI", Arial, sans-serif`;

            if (ctx.measureText(text).width <= maxWidth) {
                return size;
            }

            size -= 2;
        }

        ctx.font = `800 ${minimumSize}px "Segoe UI", Arial, sans-serif`;
        return minimumSize;
    }

    function cardStatusText(status) {
        if (status === "ACTIVE") {
            return "ACTIVE OFFICIAL";
        }

        if (status === "FORMER") {
            return "FORMER OFFICIAL";
        }

        return "POSITION VACANT";
    }

    function drawTermBox(ctx, x, y, width, label, value) {
        drawRoundRect(
            ctx,
            x,
            y,
            width,
            112,
            16,
            "rgba(255,255,255,0.075)",
            "rgba(224,190,116,0.32)"
        );

        ctx.fillStyle = "#dcb76a";
        ctx.font = '800 17px "Segoe UI", Arial, sans-serif';
        ctx.textAlign = "left";
        ctx.fillText(label, x + 23, y + 32);

        ctx.fillStyle = "#f3f6f8";
        ctx.font = '500 22px "Segoe UI", Arial, sans-serif';

        drawWrappedCardText(
            ctx,
            value || "Not recorded",
            x + 23,
            y + 70,
            width - 46,
            29,
            2,
            "left"
        );
    }

    

    
    async function renderOfficialCard(official) {
        const renderId = ++cardRenderVersion;
        const ctx = officialCardCanvas.getContext("2d");

        if (!ctx) {
            throw new Error("The browser could not prepare the official card.");
        }

        const [logo, portrait, tlcStamp] = await Promise.all([
            loadCardImage("/assets/tlc_logo.jpeg"),
            loadCardImage(
                official.photo_url && official.name
                    ? official.photo_url
                    : ""
            ),
            loadCardImage("/assets/tlc_official_stamp.jpeg")
        ]);

        if (renderId !== cardRenderVersion) return;

        if (!tlcStamp) {
            throw new Error(
                "The existing TLC stamp could not be loaded. " +
                "No substitute stamp will be used."
            );
        }

        // Landscape rectangle: 3000 wide by 1850 high.
        const W = 3000;
        const H = 1850;

        officialCardCanvas.width = W;
        officialCardCanvas.height = H;
        ctx.clearRect(0, 0, W, H);

        const status = String(official.status || "").toUpperCase();
        const approved = status === "ACTIVE" && Boolean(official.name);

        const C = {
            emerald: "#0c3b32",
            deep: "#071b25",
            gold: "#d7b56e",
            lightGold: "#f1dfb3",
            white: "#fffaf0",
            muted: "#b9c9c0",
            border: "rgba(215,181,110,0.58)"
        };

        function roundedPath(x, y, w, h, r) {
            r = Math.min(r, w / 2, h / 2);
            ctx.beginPath();
            ctx.moveTo(x + r, y);
            ctx.lineTo(x + w - r, y);
            ctx.quadraticCurveTo(x + w, y, x + w, y + r);
            ctx.lineTo(x + w, y + h - r);
            ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
            ctx.lineTo(x + r, y + h);
            ctx.quadraticCurveTo(x, y + h, x, y + h - r);
            ctx.lineTo(x, y + r);
            ctx.quadraticCurveTo(x, y, x + r, y);
            ctx.closePath();
        }

        function panel(x, y, w, h, fill, stroke = C.border, radius = 22) {
            ctx.save();
            roundedPath(x, y, w, h, radius);
            ctx.fillStyle = fill;
            ctx.fill();

            if (stroke) {
                ctx.strokeStyle = stroke;
                ctx.lineWidth = 2;
                ctx.stroke();
            }
            ctx.restore();
        }

        function rule(x1, y1, x2, y2) {
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = "rgba(215,181,110,0.4)";
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.restore();
        }

        function text(value, x, y, font, color, align = "left") {
            ctx.save();
            ctx.font = font;
            ctx.fillStyle = color;
            ctx.textAlign = align;
            ctx.textBaseline = "alphabetic";
            ctx.fillText(String(value ?? ""), x, y);
            ctx.restore();
        }

        function fitText(value, x, y, width, size, minSize, color) {
            const valueText = String(value ?? "");
            ctx.save();
            ctx.textAlign = "left";
            ctx.textBaseline = "alphabetic";

            while (size > minSize) {
                ctx.font = `700 ${size}px "Segoe UI", Arial, sans-serif`;
                if (ctx.measureText(valueText).width <= width) break;
                size -= 1;
            }

            ctx.font = `700 ${size}px "Segoe UI", Arial, sans-serif`;
            ctx.fillStyle = color;
            ctx.fillText(valueText, x, y, width);
            ctx.restore();
        }

        function wrap(value, x, y, width, lineHeight, maxLines, font, color) {
            const content = String(value ?? "").trim();
            if (!content) return 0;

            ctx.save();
            ctx.font = font;
            ctx.fillStyle = color;
            ctx.textAlign = "left";
            ctx.textBaseline = "alphabetic";

            const lines = [];
            let current = "";

            function splitLongWord(word) {
                let part = "";
                for (const character of word) {
                    const candidate = part + character;
                    if (
                        part &&
                        ctx.measureText(candidate).width > width
                    ) {
                        lines.push(part);
                        part = character;
                    } else {
                        part = candidate;
                    }
                }
                return part;
            }

            for (const word of content.split(/\s+/)) {
                const candidate = current ? current + " " + word : word;

                if (ctx.measureText(candidate).width <= width) {
                    current = candidate;
                    continue;
                }

                if (current) {
                    lines.push(current);
                    current = "";
                }

                if (ctx.measureText(word).width > width) {
                    current = splitLongWord(word);
                } else {
                    current = word;
                }
            }

            if (current) lines.push(current);

            const visible = lines.slice(0, maxLines);

            if (lines.length > maxLines && visible.length) {
                let last = visible[visible.length - 1];

                while (
                    last.length > 3 &&
                    ctx.measureText(last + "...").width > width
                ) {
                    last = last.slice(0, -1);
                }

                visible[visible.length - 1] = last + "...";
            }

            visible.forEach((item, i) => {
                ctx.fillText(item, x, y + i * lineHeight, width);
            });

            ctx.restore();
            return visible.length;
        }

        function circleImage(image, cx, cy, radius, fallback = "TLC") {
            ctx.save();
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.clip();

            const iw = image && (image.naturalWidth || image.width);
            const ih = image && (image.naturalHeight || image.height);

            if (image && iw > 0 && ih > 0) {
                const diameter = radius * 2;
                const scale = Math.max(diameter / iw, diameter / ih);
                const dw = iw * scale;
                const dh = ih * scale;
                ctx.drawImage(image, cx - dw / 2, cy - dh / 2, dw, dh);
            } else {
                ctx.fillStyle = C.emerald;
                ctx.fillRect(
                    cx - radius, cy - radius,
                    radius * 2, radius * 2
                );
                ctx.fillStyle = C.lightGold;
                ctx.font = '800 58px Georgia, serif';
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(fallback, cx, cy);
            }

            ctx.restore();

            ctx.save();
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.strokeStyle = C.gold;
            ctx.lineWidth = 6;
            ctx.stroke();

            ctx.beginPath();
            ctx.arc(cx, cy, radius - 10, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(241,223,179,0.8)";
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.restore();
        }

        function label(value, x, y) {
            text(
                String(value).toUpperCase(),
                x, y,
                '800 19px "Segoe UI", Arial, sans-serif',
                C.gold
            );
        }

        function title(value, x, y) {
            text(
                String(value).toUpperCase(),
                x, y,
                '800 23px "Segoe UI", Arial, sans-serif',
                C.gold
            );
        }

        // Emerald/navy gradient and understated engraving.
        const gradient = ctx.createLinearGradient(0, 0, W, H);
        gradient.addColorStop(0, "#061b1a");
        gradient.addColorStop(0.35, "#0b382f");
        gradient.addColorStop(0.72, "#102c3d");
        gradient.addColorStop(1, "#061a27");

        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, W, H);

        ctx.save();
        ctx.globalAlpha = 0.1;
        ctx.strokeStyle = C.gold;
        ctx.lineWidth = 1.5;

        for (let i = 0; i < 7; i += 1) {
            ctx.beginPath();
            ctx.ellipse(
                2600, 300,
                100 + i * 38,
                65 + i * 22,
                0.15, 0, Math.PI * 2
            );
            ctx.stroke();
        }
        ctx.restore();

        roundedPath(28, 28, W - 56, H - 56, 34);
        ctx.strokeStyle = C.gold;
        ctx.lineWidth = 5;
        ctx.stroke();

        roundedPath(45, 45, W - 90, H - 90, 26);
        ctx.strokeStyle = "rgba(241,223,179,0.45)";
        ctx.lineWidth = 2;
        ctx.stroke();

        // HEADER
        panel(70, 60, 2860, 165, "rgba(4,20,25,0.76)", C.border, 22);
        circleImage(logo, 160, 142, 57);

        text(
            "THE LEGACY CIRCLE",
            250, 125,
            '800 34px "Segoe UI", Arial, sans-serif',
            C.white
        );
        text(
            "LEADERSHIP  ?  LEGACY  ?  SERVICE",
            253, 168,
            '700 17px "Segoe UI", Arial, sans-serif',
            C.gold
        );
        text(
            "OFFICIAL LEADERSHIP RECORD",
            2870, 130,
            '800 19px "Segoe UI", Arial, sans-serif',
            C.lightGold,
            "right"
        );
        text(
            "OFFICE OF THE PRESIDENT",
            1500, 290,
            '800 38px "Segoe UI", Arial, sans-serif',
            C.lightGold,
            "center"
        );

        // IDENTITY / PORTRAIT
        panel(70, 320, 930, 785, "rgba(4,20,25,0.76)", C.border, 22);

        circleImage(
            portrait,
            535, 505, 145,
            String(official.name || "TLC")
                .trim().split(/\s+/).filter(Boolean)
                .slice(0, 2).map(part => part[0].toUpperCase())
                .join("") || "TLC"
        );

        label("OFFICIAL POSITION", 120, 710);
        wrap(
            official.position || "Leadership Office",
            120, 755, 830, 37, 2,
            '700 28px "Segoe UI", Arial, sans-serif',
            C.white
        );

        label("OFFICE HOLDER", 120, 850);
        wrap(
            official.name || "POSITION VACANT",
            120, 895, 830, 38, 2,
            '800 30px "Segoe UI", Arial, sans-serif',
            C.lightGold
        );

        label("TLC MEMBER ID", 120, 985);
        fitText(
            official.member_id || "Not recorded",
            120, 1025, 820, 28, 20, C.white
        );

        panel(
            120, 1040, 360, 42,
            approved ? "rgba(215,181,110,0.15)" : "rgba(185,201,192,0.1)",
            approved ? C.gold : "rgba(185,201,192,0.4)",
            20
        );
        text(
            approved ? "ACTIVE OFFICE HOLDER" :
                (status === "VACANT" ? "POSITION VACANT" : "FORMER OFFICE HOLDER"),
            300, 1067,
            '800 14px "Segoe UI", Arial, sans-serif',
            approved ? C.lightGold : C.muted,
            "center"
        );

        // CONTACT DETAILS
        panel(1030, 320, 1900, 335, "rgba(4,20,25,0.76)", C.border, 22);
        title("Official Contact Details", 1070, 366);

        rule(1980, 390, 1980, 625);

        label("OFFICIAL EMAIL ADDRESS", 1075, 425);
        wrap(
            official.email || "Not provided",
            1075, 470, 815, 35, 4,
            '600 25px "Segoe UI", Arial, sans-serif',
            C.white
        );

        label("CONTACT NUMBER", 2030, 425);
        wrap(
            official.contact || "Not provided",
            2030, 470, 820, 38, 4,
            '600 27px "Segoe UI", Arial, sans-serif',
            C.white
        );

        // TERM DATES
        panel(1030, 675, 1900, 255, "rgba(4,20,25,0.76)", C.border, 22);
        title("Term of Office", 1070, 720);

        panel(1065, 745, 865, 155, "rgba(255,255,255,0.04)", C.border, 17);
        panel(2005, 745, 865, 155, "rgba(255,255,255,0.04)", C.border, 17);

        label("TERM START", 1095, 790);
        wrap(
            official.term_start ? dateLabel(official.term_start) : "Not recorded",
            1095, 845, 805, 35, 2,
            '600 27px "Segoe UI", Arial, sans-serif',
            C.white
        );

        label("TERM END", 2035, 790);
        wrap(
            official.term_end ? dateLabel(official.term_end) : "Not recorded",
            2035, 845, 805, 35, 2,
            '600 27px "Segoe UI", Arial, sans-serif',
            C.white
        );

        // PROFILE / RESPONSIBILITIES
        panel(1030, 950, 1900, 155, "rgba(4,20,25,0.76)", C.border, 22);
        title("Profile & Responsibilities", 1070, 990);

        const biography = official.biography || (
            status === "VACANT"
                ? "This position is awaiting an official appointment."
                : "Official profile information has not been added yet."
        );

        wrap(
            biography,
            1070, 1030, 1800, 30, 2,
            '500 21px "Segoe UI", Arial, sans-serif',
            C.white
        );

        // LEGACY CIRCLE SIGNATURE AND EXISTING TLC STAMP
        panel(70, 1140, 2860, 365, "rgba(4,20,25,0.76)", C.border, 22);
        title("Legacy Circle Signature Mark", 115, 1185);

        ctx.save();
        ctx.strokeStyle = C.gold;
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.beginPath();
        ctx.moveTo(125, 1290);
        ctx.bezierCurveTo(170, 1220, 235, 1320, 305, 1275);
        ctx.bezierCurveTo(365, 1230, 430, 1310, 495, 1275);
        ctx.bezierCurveTo(560, 1230, 620, 1310, 690, 1276);
        ctx.bezierCurveTo(750, 1240, 815, 1305, 885, 1275);
        ctx.stroke();

        ctx.fillStyle = C.lightGold;
        ctx.font = 'italic 48px "Segoe Script", "Brush Script MT", cursive';
        ctx.textAlign = "left";
        ctx.fillText("Legacy Circle", 140, 1255, 760);

        ctx.fillStyle = C.muted;
        ctx.font = '700 15px "Segoe UI", Arial, sans-serif';
        ctx.fillText("ORGANISATIONAL SIGNATURE MARK", 125, 1340);
        ctx.restore();

        rule(1580, 1190, 1580, 1450);

        if (approved) {
            circleImage(tlcStamp, 1900, 1315, 93);

            text(
                "EXISTING TLC STAMP",
                1900, 1445,
                '800 16px "Segoe UI", Arial, sans-serif',
                C.lightGold,
                "center"
            );

            text(
                "ACTIVE OFFICE HOLDER",
                2400, 1300,
                '800 20px "Segoe UI", Arial, sans-serif',
                C.lightGold,
                "center"
            );

            text(
                "TLC official record",
                2400, 1345,
                '600 17px "Segoe UI", Arial, sans-serif',
                C.muted,
                "center"
            );
        } else {
            text(
                status === "VACANT" ? "POSITION VACANT" : "FORMER OFFICE HOLDER",
                2200, 1300,
                '800 20px "Segoe UI", Arial, sans-serif',
                C.muted,
                "center"
            );
            text(
                "No active approval",
                2200, 1345,
                '600 17px "Segoe UI", Arial, sans-serif',
                C.muted,
                "center"
            );
        }

        // DEDICATED POWERED-BY FOOTER
        panel(70, 1525, 2860, 245, "rgba(4,20,25,0.86)", C.border, 22);

        text(
            "THE LEGACY CIRCLE",
            W / 2, 1570,
            '800 21px "Segoe UI", Arial, sans-serif',
            C.lightGold,
            "center"
        );

        rule(1100, 1590, 1900, 1590);

        text(
            "POWERED BY",
            W / 2, 1625,
            '800 15px "Segoe UI", Arial, sans-serif',
            C.muted,
            "center"
        );

        text(
            "THEE ALVIN TECH SOLUTIONS",
            W / 2, 1675,
            '800 27px "Segoe UI", Arial, sans-serif',
            C.white,
            "center"
        );

        text(
            "OFFICIAL LEADERSHIP RECORD",
            W / 2, 1710,
            '600 13px "Segoe UI", Arial, sans-serif',
            C.muted,
            "center"
        );
    }

    async function openOfficialCard(official) {
        if (!official) {
            return;
        }

        currentCardOfficial = official;
        cardDialogTitle.textContent = `${official.position} Official Card`;
        cardDownloadStatus.textContent = "Preparing the card preview...";
        downloadOfficialCard.disabled = true;

        if (typeof officialCardDialog.showModal === "function") {
            if (!officialCardDialog.open) {
                officialCardDialog.showModal();
            }
        } else {
            officialCardDialog.setAttribute("open", "");
        }

        try {
            await renderOfficialCard(official);

            if (currentCardOfficial !== official) {
                return;
            }

            cardDownloadStatus.textContent =
                "Preview ready. Download the official card as a PNG image.";

            downloadOfficialCard.disabled = false;
        } catch (error) {
            cardDownloadStatus.textContent =
                error.message || "Unable to prepare the official card.";

            downloadOfficialCard.disabled = true;
        }
    }

    function closeOfficialCard() {
        cardRenderVersion += 1;
        currentCardOfficial = null;

        if (
            typeof officialCardDialog.close === "function" &&
            officialCardDialog.open
        ) {
            officialCardDialog.close();
        } else {
            officialCardDialog.removeAttribute("open");
        }
    }

    document.getElementById("closeOfficialCardDialog").addEventListener(
        "click",
        closeOfficialCard
    );

    officialCardDialog.addEventListener("click", event => {
        if (event.target === officialCardDialog) {
            closeOfficialCard();
        }
    });

    downloadOfficialCard.addEventListener("click", () => {
        if (!currentCardOfficial) {
            return;
        }

        try {
            officialCardCanvas.toBlob(blob => {
                if (!blob) {
                    cardDownloadStatus.textContent =
                        "PNG creation failed. Please open the card again and retry.";
                    return;
                }

                const fileNameBase = [
                    "TLC",
                    currentCardOfficial.key,
                    currentCardOfficial.name || "VACANT"
                ].join("_").replace(/[^a-zA-Z0-9_-]+/g, "_");

                const downloadUrl = URL.createObjectURL(blob);
                const anchor = document.createElement("a");

                anchor.href = downloadUrl;
                anchor.download = `${fileNameBase}_OFFICIAL_CARD.png`;

                document.body.appendChild(anchor);
                anchor.click();
                anchor.remove();

                window.setTimeout(
                    () => URL.revokeObjectURL(downloadUrl),
                    2000
                );

                cardDownloadStatus.textContent =
                    "PNG download started successfully.";
            }, "image/png");
        } catch (error) {
            cardDownloadStatus.textContent =
                "The browser could not export this image. Please try again.";
        }
    });

    directory.addEventListener("click", event => {
        const viewButton = event.target.closest("[data-view-key]");

        if (viewButton) {
            const official = currentState.officials.find(
                item => item.key === viewButton.dataset.viewKey
            );

            openOfficialCard(official);
            return;
        }

        const button = event.target.closest("[data-edit-key]");

        if (!button || !currentState.can_manage) {
            return;
        }

        const official = currentState.officials.find(
            item => item.key === button.dataset.editKey
        );

        openEditor(official);
    });

    document.getElementById("closeEditor").addEventListener("click", closeEditor);
    document.getElementById("cancelEditor").addEventListener("click", closeEditor);

    dialog.addEventListener("click", event => {
        if (event.target === dialog) {
            closeEditor();
        }
    });

    form.addEventListener("submit", async event => {
        event.preventDefault();

        if (!currentState.can_manage || !editedKey) {
            editorMessage.textContent = "You are not authorized to edit this record.";
            return;
        }

        const values = {};

        for (const [key, input] of Object.entries(fields)) {
            values[key] = input.value.trim();
        }

        if (values.status !== "VACANT" && !values.name) {
            editorMessage.textContent =
                "Enter the official's full name, or select Vacant.";
            fields.name.focus();
            return;
        }

        if (values.term_start && values.term_end
            && values.term_end < values.term_start) {
            editorMessage.textContent =
                "The term end date cannot be earlier than its start date.";
            fields.term_end.focus();
            return;
        }

        saveButton.disabled = true;
        saveButton.textContent = "Saving?";
        editorMessage.textContent = "";

        try {
            values.email = fields.email.value.trim();
            values.contact = fields.contact.value.trim();

            const response = await fetch(
                `/api/presidency/officials/${encodeURIComponent(editedKey)}`,
                {
                    method: "PUT",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(values)
                }
            );

            if (response.status === 401) {
                window.location.assign("/login");
                return;
            }

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(result.message || "The official record could not be saved.");
            }

            closeEditor();
            await loadDirectory();
        } catch (error) {
            editorMessage.textContent =
                error.message || "Unable to save the official record.";
        } finally {
            saveButton.disabled = false;
            saveButton.textContent = "Save official";
        }
    });

    loadDirectory();
})();
