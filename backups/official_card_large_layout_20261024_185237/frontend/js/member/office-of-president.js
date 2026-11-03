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
            loadCardImage("/assets/tlc_official_stamp_existing.jpeg")
        ]);

        if (renderId !== cardRenderVersion) {
            return;
        }

        if (!tlcStamp) {
            throw new Error(
                "The existing TLC stamp could not be loaded. " +
                "The card was not given a substitute stamp."
            );
        }

        const W = 1400;
        const H = 2050;

        officialCardCanvas.width = W;
        officialCardCanvas.height = H;

        ctx.clearRect(0, 0, W, H);

        const status = String(official.status || "").toUpperCase();
        const isApproved = status === "ACTIVE" && Boolean(official.name);

        const palette = {
            emerald: "#0c3b32",
            deep: "#071d27",
            navy: "#102d40",
            gold: "#d7b56e",
            lightGold: "#f1dfb3",
            ivory: "#f7f1e3",
            ink: "#142d2b",
            muted: "#b9c9c0",
            white: "#fffaf0",
            line: "rgba(215,181,110,0.55)"
        };

        function pathRound(x, y, w, h, r) {
            const radius = Math.min(r, w / 2, h / 2);

            ctx.beginPath();
            ctx.moveTo(x + radius, y);
            ctx.lineTo(x + w - radius, y);
            ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
            ctx.lineTo(x + w, y + h - radius);
            ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
            ctx.lineTo(x + radius, y + h);
            ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
            ctx.lineTo(x, y + radius);
            ctx.quadraticCurveTo(x, y, x + radius, y);
            ctx.closePath();
        }

        function panel(x, y, w, h, fill, stroke = palette.line, radius = 24) {
            ctx.save();
            pathRound(x, y, w, h, radius);
            ctx.fillStyle = fill;
            ctx.fill();

            if (stroke) {
                ctx.strokeStyle = stroke;
                ctx.lineWidth = 2;
                ctx.stroke();
            }
            ctx.restore();
        }

        function drawText(value, x, y, font, color, align = "left") {
            ctx.save();
            ctx.font = font;
            ctx.fillStyle = color;
            ctx.textAlign = align;
            ctx.textBaseline = "alphabetic";
            ctx.fillText(String(value ?? ""), x, y);
            ctx.restore();
        }

        function fitText(value, x, y, maxWidth, maxSize, minSize, color) {
            const text = String(value ?? "");
            let size = maxSize;

            ctx.save();
            ctx.textAlign = "left";
            ctx.textBaseline = "alphabetic";

            while (size > minSize) {
                ctx.font = `700 ${size}px "Segoe UI", Arial, sans-serif`;
                if (ctx.measureText(text).width <= maxWidth) {
                    break;
                }
                size -= 1;
            }

            ctx.fillStyle = color;
            ctx.font = `700 ${size}px "Segoe UI", Arial, sans-serif`;
            ctx.fillText(text, x, y, maxWidth);
            ctx.restore();
        }

        function drawWrapped(value, x, y, maxWidth, lineHeight,
                             maxLines, font, color) {
            const text = String(value ?? "").trim();

            if (!text) {
                return 0;
            }

            ctx.save();
            ctx.font = font;
            ctx.fillStyle = color;
            ctx.textAlign = "left";
            ctx.textBaseline = "alphabetic";

            const words = text.split(/\s+/);
            const lines = [];
            let current = "";

            function pushLongWord(word) {
                let piece = "";

                for (const character of word) {
                    const candidate = piece + character;

                    if (piece && ctx.measureText(candidate).width > maxWidth) {
                        lines.push(piece);
                        piece = character;
                    } else {
                        piece = candidate;
                    }
                }

                return piece;
            }

            for (const word of words) {
                const candidate = current ? `${current} ${word}` : word;

                if (ctx.measureText(candidate).width <= maxWidth) {
                    current = candidate;
                    continue;
                }

                if (current) {
                    lines.push(current);
                    current = "";
                }

                if (ctx.measureText(word).width > maxWidth) {
                    current = pushLongWord(word);
                } else {
                    current = word;
                }
            }

            if (current) {
                lines.push(current);
            }

            const shown = lines.slice(0, maxLines);

            if (lines.length > maxLines && shown.length) {
                let last = shown[shown.length - 1];

                while (
                    last.length > 3 &&
                    ctx.measureText(last + "...").width > maxWidth
                ) {
                    last = last.slice(0, -1);
                }

                shown[shown.length - 1] = last + "...";
            }

            shown.forEach((line, index) => {
                ctx.fillText(line, x, y + index * lineHeight, maxWidth);
            });

            ctx.restore();
            return shown.length;
        }

        function drawContained(image, x, y, w, h) {
            if (!image) return;

            const iw = image.naturalWidth || image.width;
            const ih = image.naturalHeight || image.height;

            if (!iw || !ih) return;

            const scale = Math.min(w / iw, h / ih);
            const dw = iw * scale;
            const dh = ih * scale;

            ctx.drawImage(
                image,
                x + (w - dw) / 2,
                y + (h - dh) / 2,
                dw,
                dh
            );
        }

        function drawCover(image, x, y, w, h, radius = 24) {
            ctx.save();
            pathRound(x, y, w, h, radius);
            ctx.clip();

            if (image) {
                const iw = image.naturalWidth || image.width;
                const ih = image.naturalHeight || image.height;
                const scale = Math.max(w / iw, h / ih);
                const dw = iw * scale;
                const dh = ih * scale;

                ctx.drawImage(
                    image,
                    x + (w - dw) / 2,
                    y + (h - dh) / 2,
                    dw,
                    dh
                );
            } else {
                ctx.fillStyle = "#143f36";
                ctx.fillRect(x, y, w, h);

                const name = String(official.name || "TLC");
                const marks = name
                    .split(/\s+/)
                    .filter(Boolean)
                    .slice(0, 2)
                    .map(part => part[0].toUpperCase())
                    .join("") || "TLC";

                ctx.fillStyle = palette.lightGold;
                ctx.font = '800 76px Georgia, serif';
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(marks, x + w / 2, y + h / 2);
            }

            ctx.restore();

            ctx.save();
            pathRound(x, y, w, h, radius);
            ctx.strokeStyle = palette.gold;
            ctx.lineWidth = 3;
            ctx.stroke();
            ctx.restore();
        }

        function label(value, x, y) {
            drawText(
                value.toUpperCase(),
                x,
                y,
                '800 17px "Segoe UI", Arial, sans-serif',
                palette.gold
            );
        }

        function drawDateBox(x, title, value) {
            panel(
                x, 1220, 535, 140,
                "rgba(255,255,255,0.055)",
                "rgba(215,181,110,0.35)",
                19
            );

            label(title, x + 28, 1261);
            drawWrapped(
                value || "Not recorded",
                x + 28, 1310, 475, 35, 2,
                '600 27px "Segoe UI", Arial, sans-serif',
                palette.white
            );
        }

        
        // CIRCLE-CROP: portrait and the existing TLC stamp.
        function drawCircularImage(image, cx, cy, radius) {
            ctx.save();
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.clip();

            if (image) {
                const iw = image.naturalWidth || image.width;
                const ih = image.naturalHeight || image.height;

                if (iw > 0 && ih > 0) {
                    const diameter = radius * 2;
                    const scale = Math.max(diameter / iw, diameter / ih);
                    const dw = iw * scale;
                    const dh = ih * scale;

                    ctx.drawImage(
                        image,
                        cx - dw / 2,
                        cy - dh / 2,
                        dw,
                        dh
                    );
                } else {
                    ctx.fillStyle = "#123b32";
                    ctx.fillRect(cx - radius, cy - radius, radius * 2, radius * 2);
                }
            } else {
                ctx.fillStyle = "#123b32";
                ctx.fillRect(cx - radius, cy - radius, radius * 2, radius * 2);

                const marks = String(official.name || "TLC")
                    .trim()
                    .split(/\s+/)
                    .filter(Boolean)
                    .slice(0, 2)
                    .map(part => part[0].toUpperCase())
                    .join("") || "TLC";

                ctx.fillStyle = "#f1dfb3";
                ctx.font = '800 62px Georgia, serif';
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(marks, cx, cy);
            }

            ctx.restore();

            // Double gold rim to echo the TLC heritage-card design.
            ctx.save();
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.strokeStyle = "#d7b56e";
            ctx.lineWidth = 5;
            ctx.stroke();

            ctx.beginPath();
            ctx.arc(cx, cy, radius - 9, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(241,223,179,0.78)";
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.restore();
        }

        // Rich emerald/navy background.
        const background = ctx.createLinearGradient(0, 0, W, H);
        background.addColorStop(0, "#061b1a");
        background.addColorStop(0.30, "#0b382f");
        background.addColorStop(0.67, "#102c3d");
        background.addColorStop(1, "#061a27");

        ctx.fillStyle = background;
        ctx.fillRect(0, 0, W, H);

        // Subtle engraved geometric texture.
        ctx.save();
        ctx.globalAlpha = 0.12;
        ctx.strokeStyle = palette.gold;
        ctx.lineWidth = 1.5;

        for (let ring = 0; ring < 8; ring += 1) {
            ctx.beginPath();
            ctx.ellipse(
                1170, 280,
                95 + ring * 25,
                55 + ring * 19,
                0.15, 0, Math.PI * 2
            );
            ctx.stroke();
        }

        for (let y = 110; y < H; y += 84) {
            ctx.beginPath();
            ctx.moveTo(58, y);
            ctx.lineTo(95, y + 37);
            ctx.stroke();
        }
        ctx.restore();

        // Card frames.
        pathRound(28, 28, W - 56, H - 56, 38);
        ctx.strokeStyle = palette.gold;
        ctx.lineWidth = 5;
        ctx.stroke();

        pathRound(43, 43, W - 86, H - 86, 29);
        ctx.strokeStyle = "rgba(241,223,179,0.48)";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Institutional heading.
        panel(82, 74, 1236, 165, "rgba(4,20,25,0.62)", palette.line, 27);

        if (logo) {
            ctx.save();
            ctx.beginPath();
            ctx.arc(166, 156, 58, 0, Math.PI * 2);
            ctx.fillStyle = palette.ivory;
            ctx.fill();
            ctx.restore();

            drawContained(logo, 117, 107, 98, 98);
        }

        drawText(
            "THE LEGACY CIRCLE",
            248, 135,
            '800 35px "Segoe UI", Arial, sans-serif',
            palette.white
        );

        drawText(
            "LEADERSHIP  ?  LEGACY  ?  SERVICE",
            250, 174,
            '700 17px "Segoe UI", Arial, sans-serif',
            palette.gold
        );

        drawText(
            "OFFICIAL RECORD",
            1280, 123,
            '800 18px "Segoe UI", Arial, sans-serif',
            palette.lightGold,
            "right"
        );

        drawText(
            "LEADERSHIP CARD",
            1280, 160,
            '700 16px "Segoe UI", Arial, sans-serif',
            palette.muted,
            "right"
        );

        drawText(
            "OFFICE OF THE PRESIDENT",
            W / 2, 300,
            '800 39px "Segoe UI", Arial, sans-serif',
            palette.lightGold,
            "center"
        );

        // Main identity block.
        panel(75, 335, 1250, 555, "rgba(4,20,25,0.73)", palette.line, 28);

        drawCircularImage(portrait, 309.5, 611.5, 202);

        // Thin decorative photo edge.
        pathRound(115, 378, 389, 467, 16);
        ctx.strokeStyle = "rgba(255,255,255,0.36)";
        ctx.lineWidth = 1.5;
        ctx.stroke();

        label("OFFICIAL POSITION", 562, 407);

        drawWrapped(
            official.position || "Leadership Office",
            562, 459, 710, 48, 2,
            '800 34px "Segoe UI", Arial, sans-serif',
            palette.white
        );

        label("NAME OF OFFICE HOLDER", 562, 550);

        drawWrapped(
            official.name || "POSITION VACANT",
            562, 610, 710, 54, 3,
            '800 42px "Segoe UI", Arial, sans-serif',
            palette.lightGold
        );

        label("TLC MEMBER ID", 562, 736);

        drawText(
            official.member_id || "Not recorded",
            562, 780,
            '600 28px "Segoe UI", Arial, sans-serif',
            palette.white
        );

        const statusLabel = isApproved
            ? "ACTIVE OFFICE HOLDER"
            : (status === "VACANT" ? "POSITION VACANT" : "FORMER OFFICE HOLDER");

        const badgeWidth = isApproved ? 300 : 270;

        panel(
            562, 815, badgeWidth, 44,
            isApproved ? "rgba(215,181,110,0.16)" : "rgba(180,190,185,0.10)",
            isApproved ? palette.gold : "rgba(185,201,192,0.35)",
            20
        );

        drawText(
            statusLabel,
            562 + badgeWidth / 2,
            843,
            '800 15px "Segoe UI", Arial, sans-serif',
            isApproved ? palette.lightGold : palette.muted,
            "center"
        );

        // Dedicated, readable contact section.
        panel(75, 920, 1250, 250, "rgba(4,20,25,0.68)", palette.line, 24);

        label("OFFICIAL CONTACT DETAILS", 108, 964);

        ctx.save();
        ctx.strokeStyle = "rgba(215,181,110,0.35)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(700, 985);
        ctx.lineTo(700, 1143);
        ctx.stroke();
        ctx.restore();

        label("OFFICIAL EMAIL", 112, 1012);

        drawWrapped(
            official.email || "Not provided",
            112, 1060, 535, 34, 3,
            '600 25px "Segoe UI", Arial, sans-serif',
            palette.white
        );

        label("CONTACT NUMBER", 744, 1012);

        drawWrapped(
            official.contact || "Not provided",
            744, 1060, 525, 34, 3,
            '600 28px "Segoe UI", Arial, sans-serif',
            palette.white
        );

        // Separate term boxes.
        label("TERM OF OFFICE", 105, 1200);

        drawDateBox(
            95,
            "TERM START",
            official.term_start ? dateLabel(official.term_start) : "Not recorded"
        );

        drawDateBox(
            770,
            "TERM END",
            official.term_end ? dateLabel(official.term_end) : "Not recorded"
        );

        // Profile gets its own large, uncluttered panel.
        panel(75, 1395, 1250, 250, "rgba(4,20,25,0.66)", palette.line, 24);

        label("PROFILE & RESPONSIBILITIES", 110, 1442);

        const biography = official.biography || (
            status === "VACANT"
                ? "This position is awaiting an official appointment."
                : "Official profile information has not been added yet."
        );

        drawWrapped(
            biography,
            110, 1492, 1168, 34, 4,
            '500 25px "Segoe UI", Arial, sans-serif',
            palette.white
        );

        // Legacy signature artwork and the REAL existing TLC stamp.
        panel(75, 1670, 1250, 265, "rgba(4,20,25,0.70)", palette.line, 24);

        label("LEGACY CIRCLE SIGNATURE", 118, 1720);

        ctx.save();
        ctx.strokeStyle = palette.gold;
        ctx.lineWidth = 3.5;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";

        ctx.beginPath();
        ctx.moveTo(135, 1810);
        ctx.bezierCurveTo(165, 1762, 205, 1839, 255, 1797);
        ctx.bezierCurveTo(288, 1770, 314, 1830, 351, 1795);
        ctx.bezierCurveTo(393, 1760, 425, 1821, 468, 1794);
        ctx.bezierCurveTo(505, 1771, 535, 1818, 581, 1792);
        ctx.stroke();

        ctx.fillStyle = palette.lightGold;
        ctx.font = 'italic 48px "Segoe Script", "Brush Script MT", cursive';
        ctx.textAlign = "left";
        ctx.fillText("Legacy Circle", 148, 1790, 450);

        ctx.fillStyle = palette.muted;
        ctx.font = '700 14px "Segoe UI", Arial, sans-serif';
        ctx.fillText("ORGANISATIONAL SIGNATURE MARK", 135, 1850);
        ctx.restore();

        if (isApproved) {
            // Use the existing TLC stamp asset; do not draw a substitute seal.
            ctx.save();
            ctx.fillStyle = palette.ivory;
            ctx.beginPath();
            ctx.arc(1138, 1800, 96, 0, Math.PI * 2);
            ctx.fill();

            ctx.strokeStyle = palette.gold;
            ctx.lineWidth = 3;
            ctx.stroke();

            drawCircularImage(tlcStamp, 1138, 1800, 80);
            ctx.restore();

            drawText(
                "TLC APPROVAL STAMP",
                1138, 1908,
                '800 15px "Segoe UI", Arial, sans-serif',
                palette.lightGold,
                "center"
            );
        } else {
            drawText(
                status === "VACANT" ? "POSITION VACANT" : "FORMER OFFICE HOLDER",
                1138, 1800,
                '800 20px "Segoe UI", Arial, sans-serif',
                palette.muted,
                "center"
            );
        }

        // Footer.
        ctx.save();
        ctx.strokeStyle = "rgba(215,181,110,0.38)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(100, 1960);
        ctx.lineTo(1300, 1960);
        ctx.stroke();
        ctx.restore();

        drawText(
            "THE LEGACY CIRCLE",
            700, 1994,
            '800 21px "Segoe UI", Arial, sans-serif',
            palette.lightGold,
            "center"
        );

        drawText(
            "POWERED BY THEE ALVIN TECH SOLUTIONS",
            700, 2020,
            '700 13px "Segoe UI", Arial, sans-serif',
            palette.muted,
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
