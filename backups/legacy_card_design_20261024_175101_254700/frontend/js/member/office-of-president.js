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

        const logoPromise = loadCardImage("/assets/tlc_logo.jpeg");
        const portraitPromise = loadCardImage(
            official.photo_url && official.name
                ? official.photo_url
                : ""
        );

        const [logo, portrait] = await Promise.all([
            logoPromise,
            portraitPromise
        ]);

        if (renderId !== cardRenderVersion) {
            return;
        }

        const width = 1200;
        const height = 1500;

        officialCardCanvas.width = width;
        officialCardCanvas.height = height;

        ctx.clearRect(0, 0, width, height);

        // Deep navy background with a subtle teal glow.
        const background = ctx.createLinearGradient(0, 0, width, height);
        background.addColorStop(0, "#091a2a");
        background.addColorStop(0.58, "#12354a");
        background.addColorStop(1, "#0e514f");

        ctx.fillStyle = background;
        ctx.fillRect(0, 0, width, height);

        // Fine decorative circles.
        ctx.save();
        ctx.strokeStyle = "rgba(224,190,116,0.10)";
        ctx.lineWidth = 2;

        for (let i = 0; i < 5; i++) {
            ctx.beginPath();
            ctx.arc(1090, 185, 115 + i * 42, 0, Math.PI * 2);
            ctx.stroke();
        }

        ctx.restore();

        // Gold frame.
        roundedPath(ctx, 28, 28, width - 56, height - 56, 28);
        ctx.strokeStyle = "#dcb76a";
        ctx.lineWidth = 3;
        ctx.stroke();

        roundedPath(ctx, 43, 43, width - 86, height - 86, 20);
        ctx.strokeStyle = "rgba(220,183,106,0.35)";
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Official TLC logo, contained in a white tile.
        drawRoundRect(ctx, 77, 75, 112, 112, 19, "#ffffff");

        if (!drawImageContained(ctx, logo, 86, 84, 94, 94)) {
            ctx.fillStyle = "#15344a";
            ctx.font = '900 28px "Segoe UI", Arial, sans-serif';
            ctx.textAlign = "center";
            ctx.fillText("TLC", 133, 143);
        }

        ctx.textAlign = "left";
        ctx.fillStyle = "#ffffff";
        ctx.font = '800 31px "Segoe UI", Arial, sans-serif';
        ctx.fillText("THE LEGACY CIRCLE", 215, 116);

        ctx.fillStyle = "#dcb76a";
        ctx.font = '700 17px "Segoe UI", Arial, sans-serif';
        ctx.fillText("OFFICIAL LEADERSHIP CARD", 216, 153);

        // Status badge.
        const badgeText = cardStatusText(official.status);
        ctx.font = '800 16px "Segoe UI", Arial, sans-serif';

        const badgeWidth = Math.max(
            210,
            ctx.measureText(badgeText).width + 42
        );

        const badgeX = width - 82 - badgeWidth;

        const badgeColor = official.status === "ACTIVE"
            ? "#1c765b"
            : official.status === "FORMER"
                ? "#53677a"
                : "#7c602e";

        drawRoundRect(
            ctx,
            badgeX,
            92,
            badgeWidth,
            48,
            24,
            badgeColor,
            "rgba(255,255,255,0.30)"
        );

        ctx.fillStyle = "#ffffff";
        ctx.textAlign = "center";
        ctx.fillText(
            badgeText,
            badgeX + badgeWidth / 2,
            122
        );

        // Header rule.
        ctx.strokeStyle = "rgba(220,183,106,0.55)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(78, 220);
        ctx.lineTo(width - 78, 220);
        ctx.stroke();

        // Position title.
        ctx.fillStyle = "#dcb76a";
        ctx.font = '800 21px "Segoe UI", Arial, sans-serif';
        ctx.textAlign = "center";

        ctx.fillText(
            String(official.position || "TLC OFFICIAL").toUpperCase(),
            width / 2,
            275
        );

        // Official photograph or initials fallback.
        const centerX = width / 2;
        const centerY = 455;
        const radius = 117;

        ctx.save();
        ctx.shadowColor = "rgba(0,0,0,0.32)";
        ctx.shadowBlur = 24;
        ctx.shadowOffsetY = 8;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius + 8, 0, Math.PI * 2);
        ctx.fillStyle = "#dcb76a";
        ctx.fill();
        ctx.restore();

        ctx.save();
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.clip();

        const portraitBackground = ctx.createLinearGradient(
            centerX - radius,
            centerY - radius,
            centerX + radius,
            centerY + radius
        );

        portraitBackground.addColorStop(0, "#f7efd9");
        portraitBackground.addColorStop(1, "#dce8e8");

        ctx.fillStyle = portraitBackground;
        ctx.fillRect(
            centerX - radius,
            centerY - radius,
            radius * 2,
            radius * 2
        );

        if (!drawImageCover(
            ctx,
            portrait,
            centerX - radius,
            centerY - radius,
            radius * 2,
            radius * 2
        )) {
            ctx.fillStyle = "#896e39";
            ctx.font = '800 75px "Segoe UI", Arial, sans-serif';
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(initials(official.name), centerX, centerY);
            ctx.textBaseline = "alphabetic";
        }

        ctx.restore();

        ctx.beginPath();
        ctx.arc(centerX, centerY, radius + 8, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(255,255,255,0.95)";
        ctx.lineWidth = 3;
        ctx.stroke();

        // Name/title block.
        const displayName = official.name || (
            official.status === "FORMER"
                ? "FORMER OFFICE HOLDER"
                : "POSITION VACANT"
        );

        ctx.textAlign = "center";
        ctx.fillStyle = "#ffffff";

        const nameFontSize = fitCardText(
            ctx,
            displayName.toUpperCase(),
            1000,
            59,
            37
        );

        ctx.font = `800 ${nameFontSize}px "Segoe UI", Arial, sans-serif`;

        const nameLines = drawWrappedCardText(
            ctx,
            displayName.toUpperCase(),
            centerX,
            650,
            1000,
            67,
            2,
            "center"
        );

        let nextY = 650 + nameLines * 67;

        if (official.member_id && official.name) {
            ctx.fillStyle = "#c6d4df";
            ctx.font = '500 23px "Segoe UI", Arial, sans-serif';

            ctx.fillText(
                `MEMBER ID: ${official.member_id}`,
                centerX,
                nextY + 26
            );

            nextY += 50;
        }

        const separatorY = Math.max(755, nextY + 22);

        ctx.strokeStyle = "rgba(220,183,106,0.40)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(100, separatorY);
        ctx.lineTo(width - 100, separatorY);
        ctx.stroke();

        // Term details.
        const termY = separatorY + 26;

        drawTermBox(
            ctx,
            92,
            termY,
            492,
            "TERM START",
            dateLabel(official.term_start) || "Not recorded"
        );

        drawTermBox(
            ctx,
            616,
            termY,
            492,
            "TERM END",
            dateLabel(official.term_end) || "Not recorded"
        );

        // Biography / profile.
        const profileY = termY + 165;

        ctx.textAlign = "left";
        ctx.fillStyle = "#dcb76a";
        ctx.font = '800 17px "Segoe UI", Arial, sans-serif';
        ctx.fillText("OFFICIAL PROFILE", 100, profileY);

        ctx.fillStyle = "#e2e9ee";
        ctx.font = '400 21px "Segoe UI", Arial, sans-serif';

        const biography = official.biography || (
            official.status === "VACANT"
                ? "This position is awaiting an official appointment."
                : "Official profile information has not been added yet."
        );

        drawWrappedCardText(
            ctx,
            biography,
            100,
            profileY + 43,
            1000,
            33,
            4,
            "left"
        );

        // Formal footer.
        const footerLineY = height - 126;

        ctx.strokeStyle = "rgba(220,183,106,0.50)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(100, footerLineY);
        ctx.lineTo(width - 100, footerLineY);
        ctx.stroke();

        ctx.textAlign = "center";
        ctx.fillStyle = "#dcb76a";
        ctx.font = '800 16px "Segoe UI", Arial, sans-serif';

        ctx.fillText(
            "THE LEGACY CIRCLE",
            centerX,
            height - 84
        );

        ctx.fillStyle = "#bdcbd6";
        ctx.font = '500 14px "Segoe UI", Arial, sans-serif';

        ctx.fillText(
            "OFFICIAL LEADERSHIP DIRECTORY",
            centerX,
            height - 57
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
