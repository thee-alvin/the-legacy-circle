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
            throw new Error("Your browser could not prepare the card image.");
        }

        const [logo, portrait] = await Promise.all([
            loadCardImage("/assets/tlc_logo.jpeg"),
            loadCardImage(
                official.photo_url && official.name
                    ? official.photo_url
                    : ""
            )
        ]);

        if (renderId !== cardRenderVersion) {
            return;
        }

        // ----------------------------------------------------
        // TLC LEGACY CARD
        // 1200 x 1500 px - high-resolution portrait PNG
        // Design: emerald, midnight navy, ivory and antique gold
        // ----------------------------------------------------

        const W = 1200;
        const H = 1500;
        const cx = W / 2;

        officialCardCanvas.width = W;
        officialCardCanvas.height = H;

        ctx.clearRect(0, 0, W, H);

        // Deep emerald-to-midnight background.
        const background = ctx.createLinearGradient(0, 0, W, H);
        background.addColorStop(0, "#061b1a");
        background.addColorStop(0.33, "#0b382f");
        background.addColorStop(0.68, "#102c3d");
        background.addColorStop(1, "#061a27");

        ctx.fillStyle = background;
        ctx.fillRect(0, 0, W, H);

        // Restrained atmospheric glow.
        const glow = ctx.createRadialGradient(
            1030, 230, 5, 1030, 230, 410
        );
        glow.addColorStop(0, "rgba(197,155,72,0.19)");
        glow.addColorStop(1, "rgba(197,155,72,0)");

        ctx.fillStyle = glow;
        ctx.fillRect(570, 0, 630, 570);

        // Guilloche-inspired engraved curves.
        // Decorative only; they do not imitate a real banknote.
        ctx.save();
        ctx.lineWidth = 1;

        for (const baseY of [235, 1230]) {
            for (let band = 0; band < 6; band++) {
                ctx.beginPath();

                for (let x = 60; x <= 1140; x += 4) {
                    const y =
                        baseY +
                        band * 5 +
                        Math.sin(x / 28 + band * 0.65) * 3;

                    if (x === 60) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                }

                ctx.strokeStyle = band % 2 === 0
                    ? "rgba(220,183,106,0.15)"
                    : "rgba(213,232,218,0.075)";

                ctx.stroke();
            }
        }

        // Fine diagonal security-style linework.
        ctx.strokeStyle = "rgba(220,183,106,0.055)";
        ctx.lineWidth = 1;

        for (let x = -H; x < W + H; x += 46) {
            ctx.beginPath();
            ctx.moveTo(x, 260);
            ctx.lineTo(x + 250, 0);
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(x, H);
            ctx.lineTo(x + 180, H - 250);
            ctx.stroke();
        }

        ctx.restore();

        // Double gold frame with fine inner ivory line.
        roundedPath(ctx, 27, 27, W - 54, H - 54, 31);
        ctx.strokeStyle = "#d5af62";
        ctx.lineWidth = 3;
        ctx.stroke();

        roundedPath(ctx, 40, 40, W - 80, H - 80, 25);
        ctx.strokeStyle = "rgba(241,220,170,0.44)";
        ctx.lineWidth = 1.2;
        ctx.stroke();

        roundedPath(ctx, 51, 51, W - 102, H - 102, 20);
        ctx.strokeStyle = "rgba(220,183,106,0.2)";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Corner filigree rosettes.
        for (const corner of [
            [78, 78],
            [1122, 78],
            [78, 1422],
            [1122, 1422]
        ]) {
            const [x, y] = corner;

            ctx.save();
            ctx.translate(x, y);
            ctx.strokeStyle = "rgba(220,183,106,0.7)";
            ctx.lineWidth = 1.3;

            for (let ring = 0; ring < 3; ring++) {
                ctx.beginPath();
                ctx.arc(0, 0, 8 + ring * 7, 0, Math.PI * 2);
                ctx.stroke();
            }

            ctx.restore();
        }

        // ----------------------------------------------------
        // HEADER AND OFFICIAL TLC BRANDING
        // ----------------------------------------------------

        drawRoundRect(
            ctx, 78, 75, 106, 106, 19, "#ffffff", "#d5af62"
        );

        if (!drawImageContained(ctx, logo, 85, 82, 92, 92)) {
            ctx.textAlign = "center";
            ctx.fillStyle = "#143b33";
            ctx.font = '900 30px "Segoe UI", Arial, sans-serif';
            ctx.fillText("TLC", 131, 139);
        }

        ctx.textAlign = "left";
        ctx.fillStyle = "#f7f0df";
        ctx.font = '800 29px "Segoe UI", Arial, sans-serif';
        ctx.fillText("THE LEGACY CIRCLE", 210, 118);

        ctx.fillStyle = "#d9b970";
        ctx.font = '700 14px "Segoe UI", Arial, sans-serif';
        ctx.fillText("OFFICIAL LEADERSHIP SERIES", 212, 151);

        // Coin-inspired heritage medallion.
        // It represents TLC identity, not legal tender.
        const coinX = 1037;
        const coinY = 130;

        const coinGradient = ctx.createRadialGradient(
            coinX - 20, coinY - 24, 3,
            coinX, coinY, 72
        );

        coinGradient.addColorStop(0, "#fff0bf");
        coinGradient.addColorStop(0.36, "#d9b56c");
        coinGradient.addColorStop(0.69, "#9f7935");
        coinGradient.addColorStop(1, "#e7ca82");

        ctx.beginPath();
        ctx.arc(coinX, coinY, 58, 0, Math.PI * 2);
        ctx.fillStyle = coinGradient;
        ctx.fill();

        ctx.strokeStyle = "#f2dfa6";
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(coinX, coinY, 49, 0, Math.PI * 2);
        ctx.strokeStyle = "#896629";
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(coinX, coinY, 42, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(92,65,25,0.48)";
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.textAlign = "center";
        ctx.fillStyle = "#28372b";
        ctx.font = '900 28px "Segoe UI", Arial, sans-serif';
        ctx.fillText("LC", coinX, coinY + 5);

        ctx.fillStyle = "#4a3a1d";
        ctx.font = '800 8px "Segoe UI", Arial, sans-serif';
        ctx.fillText("LEGACY", coinX, coinY + 27);

        // Header title.
        ctx.textAlign = "center";
        ctx.fillStyle = "#dcb76a";
        ctx.font = '800 17px "Segoe UI", Arial, sans-serif';
        ctx.fillText("OFFICIAL LEADERSHIP CARD", cx, 260);

        ctx.fillStyle = "#d2dfd9";
        ctx.font = '500 12px "Segoe UI", Arial, sans-serif';
        ctx.fillText("TRUST  |  SERVICE  |  LEGACY", cx, 287);

        // Small gold center divider.
        ctx.strokeStyle = "#dcb76a";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(475, 307);
        ctx.lineTo(725, 307);
        ctx.stroke();

        // ----------------------------------------------------
        // IVORY IDENTITY PANEL
        // ----------------------------------------------------

        const panelX = 72;
        const panelY = 337;
        const panelW = 1056;
        const panelH = 453;

        ctx.save();
        ctx.shadowColor = "rgba(0,0,0,0.30)";
        ctx.shadowBlur = 22;
        ctx.shadowOffsetY = 8;

        drawRoundRect(
            ctx,
            panelX,
            panelY,
            panelW,
            panelH,
            24,
            "#f7f0df",
            "#dcb76a"
        );

        ctx.restore();

        // Fine engraved lines on the ivory panel.
        ctx.save();
        ctx.beginPath();
        roundedPath(ctx, panelX + 12, panelY + 12, panelW - 24, panelH - 24, 18);
        ctx.clip();

        ctx.strokeStyle = "rgba(118,93,49,0.055)";
        ctx.lineWidth = 1;

        for (let x = panelX; x <= panelX + panelW; x += 18) {
            ctx.beginPath();
            ctx.moveTo(x, panelY + 10);
            ctx.lineTo(x + 70, panelY + panelH - 10);
            ctx.stroke();
        }

        ctx.restore();

        // Portrait medallion.
        const portraitX = 251;
        const portraitY = 557;
        const portraitR = 119;

        ctx.save();
        ctx.shadowColor = "rgba(26,38,29,0.24)";
        ctx.shadowBlur = 18;
        ctx.shadowOffsetY = 6;

        ctx.beginPath();
        ctx.arc(portraitX, portraitY, portraitR + 9, 0, Math.PI * 2);

        const portraitRing = ctx.createLinearGradient(
            portraitX - portraitR,
            portraitY - portraitR,
            portraitX + portraitR,
            portraitY + portraitR
        );

        portraitRing.addColorStop(0, "#fff0bf");
        portraitRing.addColorStop(0.5, "#b58a3d");
        portraitRing.addColorStop(1, "#e6c879");

        ctx.fillStyle = portraitRing;
        ctx.fill();

        ctx.restore();

        // Double portrait edge.
        ctx.beginPath();
        ctx.arc(portraitX, portraitY, portraitR + 4, 0, Math.PI * 2);
        ctx.strokeStyle = "#b48b45";
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.save();
        ctx.beginPath();
        ctx.arc(portraitX, portraitY, portraitR, 0, Math.PI * 2);
        ctx.clip();

        const portraitBackground = ctx.createLinearGradient(
            portraitX - portraitR,
            portraitY - portraitR,
            portraitX + portraitR,
            portraitY + portraitR
        );

        portraitBackground.addColorStop(0, "#f5e7c6");
        portraitBackground.addColorStop(1, "#d8e7df");

        ctx.fillStyle = portraitBackground;
        ctx.fillRect(
            portraitX - portraitR,
            portraitY - portraitR,
            portraitR * 2,
            portraitR * 2
        );

        if (!drawImageCover(
            ctx,
            portrait,
            portraitX - portraitR,
            portraitY - portraitR,
            portraitR * 2,
            portraitR * 2
        )) {
            const initialsText = official.name
                ? initials(official.name)
                : "LC";

            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "#775d2f";
            ctx.font = '900 65px "Segoe UI", Arial, sans-serif';

            ctx.fillText(initialsText, portraitX, portraitY);

            ctx.textBaseline = "alphabetic";
        }

        ctx.restore();

        // Vertical gold divider.
        ctx.beginPath();
        ctx.moveTo(421, 390);
        ctx.lineTo(421, 735);
        ctx.strokeStyle = "rgba(158,123,57,0.38)";
        ctx.lineWidth = 1.4;
        ctx.stroke();

        // Position label.
        ctx.textAlign = "left";
        ctx.fillStyle = "#92702f";
        ctx.font = '800 13px "Segoe UI", Arial, sans-serif';

        ctx.fillText(
            String(official.position || "TLC OFFICIAL").toUpperCase(),
            463,
            414
        );

        // Name: large enough to be prominent but constrained to panel.
        const name = official.name || (
            official.status === "FORMER"
                ? "Former Office Holder"
                : "Position Vacant"
        );

        const nameUpper = name.toUpperCase();

        const nameFontSize = fitCardText(
            ctx,
            nameUpper,
            585,
            46,
            29
        );

        ctx.font = `800 ${nameFontSize}px "Segoe UI", Arial, sans-serif`;
        ctx.fillStyle = "#17372f";

        const nameLines = drawWrappedCardText(
            ctx,
            nameUpper,
            463,
            481,
            585,
            53,
            2,
            "left"
        );

        const memberBaseline = 481 + nameLines * 53 + 12;

        if (official.member_id && official.name) {
            ctx.fillStyle = "#5a6a5e";
            ctx.font = '600 15px "Segoe UI", Arial, sans-serif';

            ctx.fillText(
                `MEMBER ID: ${official.member_id}`,
                464,
                Math.min(memberBaseline, 621)
            );
        }

        // Status plaque.
        const badgeText = cardStatusText(official.status);

        ctx.font = '800 11px "Segoe UI", Arial, sans-serif';

        const badgeW = Math.max(
            165,
            ctx.measureText(badgeText).width + 32
        );

        const badgeColor = official.status === "ACTIVE"
            ? "#1f6b4f"
            : official.status === "FORMER"
                ? "#586778"
                : "#917033";

        drawRoundRect(
            ctx,
            463,
            679,
            badgeW,
            35,
            17,
            badgeColor,
            null
        );

        ctx.textAlign = "center";
        ctx.fillStyle = "#ffffff";
        ctx.fillText(
            badgeText,
            463 + badgeW / 2,
            701
        );

        ctx.textAlign = "left";
        ctx.fillStyle = "#8c7952";
        ctx.font = '700 9px "Segoe UI", Arial, sans-serif';
        ctx.fillText("THE LEGACY CIRCLE", 463, 752);

        // ----------------------------------------------------
        // TERM OF OFFICE PANELS
        // ----------------------------------------------------

        const termY = 823;

        drawTermBox(
            ctx,
            77,
            termY,
            507,
            "TERM START",
            dateLabel(official.term_start) || "Not recorded"
        );

        drawTermBox(
            ctx,
            616,
            termY,
            507,
            "TERM END",
            dateLabel(official.term_end) || "Not recorded"
        );

        // ----------------------------------------------------
        // OFFICIAL PROFILE PANEL
        // ----------------------------------------------------

        drawRoundRect(
            ctx,
            76,
            972,
            1048,
            232,
            19,
            "#0c302e",
            "rgba(220,183,106,0.52)"
        );

        // Small gold vertical accent.
        drawRoundRect(
            ctx,
            98,
            1000,
            4,
            35,
            2,
            "#dcb76a",
            null
        );

        ctx.textAlign = "left";
        ctx.fillStyle = "#e1c37f";
        ctx.font = '800 14px "Segoe UI", Arial, sans-serif';
        ctx.fillText("OFFICIAL PROFILE", 117, 1022);

        ctx.fillStyle = "#e7eee9";
        ctx.font = '400 19px "Segoe UI", Arial, sans-serif';

        const biography = official.biography || (
            official.status === "VACANT"
                ? "This position is awaiting an official appointment."
                : "Official profile information has not been added yet."
        );

        drawWrappedCardText(
            ctx,
            biography,
            117,
            1065,
            966,
            28,
            4,
            "left"
        );

        // Subtle money-and-legacy coin watermark.
        ctx.save();
        ctx.globalAlpha = 0.10;
        ctx.strokeStyle = "#dfc17b";
        ctx.lineWidth = 2;

        for (const radius of [27, 36, 45]) {
            ctx.beginPath();
            ctx.arc(1052, 1150, radius, 0, Math.PI * 2);
            ctx.stroke();
        }

        ctx.globalAlpha = 0.20;
        ctx.fillStyle = "#dfc17b";
        ctx.textAlign = "center";
        ctx.font = '800 19px "Segoe UI", Arial, sans-serif';
        ctx.fillText("LC", 1052, 1157);

        ctx.restore();

        // ----------------------------------------------------
        // TECHNOLOGY BRANDING AND FORMAL FOOTER
        // ----------------------------------------------------

        ctx.strokeStyle = "rgba(220,183,106,0.58)";
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.moveTo(185, 1260);
        ctx.lineTo(1015, 1260);
        ctx.stroke();

        ctx.textAlign = "center";
        ctx.fillStyle = "#c0cdbf";
        ctx.font = '600 12px "Segoe UI", Arial, sans-serif';
        ctx.fillText("POWERED BY", cx, 1300);

        ctx.fillStyle = "#e5c67c";
        ctx.font = '800 22px "Segoe UI", Arial, sans-serif';
        ctx.fillText("THEE ALVIN TECH SOLUTIONS", cx, 1338);

        ctx.fillStyle = "#d4e0db";
        ctx.font = '600 10px "Segoe UI", Arial, sans-serif';
        ctx.fillText("TLC OFFICIAL LEADERSHIP  |  TRUST  |  SERVICE  |  LEGACY", cx, 1372);

        ctx.fillStyle = "rgba(232,238,231,0.58)";
        ctx.font = '500 10px "Segoe UI", Arial, sans-serif';
        ctx.fillText("THE LEGACY CIRCLE", cx, 1404);
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
