const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");

const messagesContainer =
    document.getElementById("chatContainer") ||
    document.querySelector(".mx-auto.max-w-3xl");

// ==================================================
// JWT SESSION
// ==================================================

const token = localStorage.getItem("token");

// No token -> back to the login page.
if (!token) {
    window.location.replace("/login");
}

// ==================================================
// BASIC HELPERS
// ==================================================

function scrollToBottom() {
    const container = messagesContainer.parentElement;
    container.scrollTop = container.scrollHeight;
}

function addText(parent, text, className = "") {
    const element = document.createElement("div");
    element.className = className;
    element.textContent = text;
    parent.appendChild(element);
    return element;
}

// ==================================================
// MARKDOWN RENDERING
// ==================================================

let markedReady = false;

function ensureMarked() {
    if (!markedReady && typeof marked !== "undefined") {
        marked.use({
            gfm: true,
            breaks: true,
            headerIds: false,
            mangle: false,
        });
        markedReady = true;
    }
}

function renderMarkdown(text) {
    ensureMarked();
    if (typeof marked === "undefined") {
        return renderFallbackMarkdown(normalizeMarkdownTables(text || ""));
    }
    return marked.parse(normalizeMarkdownTables(text || ""));
}

function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = value;
    return element.innerHTML;
}

function tableCells(line) {
    return line.trim().replace(/^\||\|$/g, "").split("|").map((cell) =>
        escapeHtml(cell.trim())
    );
}

// Keep the chat usable when a CDN is blocked by a browser, proxy, or CSP.
// This deliberately implements the small Markdown subset needed for chat
// responses and, unlike the previous raw-HTML fallback, never injects model
// output directly into the page.
function renderFallbackMarkdown(text) {
    const lines = text.split("\n");
    const output = [];

    for (let index = 0; index < lines.length; index += 1) {
        const header = lines[index];
        const expectedCells = isTableRow(header) ? tableCellCount(header) : 0;

        if (expectedCells && isTableSeparator(lines[index + 1] || "", expectedCells)) {
            const headers = tableCells(header);
            const rows = [];
            index += 2;

            while (index < lines.length && isTableRow(lines[index])) {
                const cells = tableCells(lines[index]);
                while (cells.length < expectedCells) {
                    cells.push("");
                }
                rows.push(`<tr>${cells.slice(0, expectedCells).map((cell) => `<td>${cell}</td>`).join("")}</tr>`);
                index += 1;
            }

            output.push(
                `<table><thead><tr>${headers.map((cell) => `<th>${cell}</th>`).join("")}</tr></thead>` +
                `<tbody>${rows.join("")}</tbody></table>`
            );
            index -= 1;
            continue;
        }

        if (header.trim()) {
            output.push(`<p>${escapeHtml(header)}</p>`);
        }
    }

    return output.join("\n");
}

function isTableRow(line) {
    const trimmed = line.trim();
    return trimmed.includes("|") && !trimmed.startsWith("```") &&
        /^\|?.+\|.+\|?$/.test(trimmed);
}

function tableCellCount(line) {
    return line.trim().replace(/^\||\|$/g, "").split("|").length;
}

function isTableSeparator(line, expectedCells) {
    const cells = line.trim().replace(/^\||\|$/g, "").split("|");
    return cells.length === expectedCells && cells.every((cell) =>
        /^\s*:?-{3,}:?\s*$/.test(cell)
    );
}

// Models occasionally emit a pipe-delimited line while it is still
// streaming, or omit one trailing empty cell.  Only pass a block to the
// Markdown table parser when it has a valid header/separator pair; repair
// harmless missing trailing cells so the final table remains rectangular.
function normalizeMarkdownTables(text) {
    const lines = text.replace(/\r\n?/g, "\n").split("\n");

    for (let index = 0; index < lines.length - 1; index += 1) {
        if (!isTableRow(lines[index])) {
            continue;
        }

        const expectedCells = tableCellCount(lines[index]);
        if (!isTableSeparator(lines[index + 1], expectedCells)) {
            continue;
        }

        for (let row = index + 2; row < lines.length && isTableRow(lines[row]); row += 1) {
            const actualCells = tableCellCount(lines[row]);
            if (actualCells < expectedCells) {
                lines[row] = `${lines[row].trim().replace(/\|?$/, "|")}${"|".repeat(expectedCells - actualCells)}`;
            }
        }
    }

    return lines.join("\n");
}

function updateAnswer(answerElement, html) {
    answerElement.innerHTML = html;

    // Wrap tables in responsive containers
    answerElement.querySelectorAll("table").forEach((table) => {
        if (table.parentElement?.classList.contains("table-wrap")) {
            return;
        }
        const wrap = document.createElement("div");
        wrap.className = "table-wrap";
        table.parentNode.insertBefore(wrap, table);
        wrap.appendChild(table);
    });
}

// ==================================================
// USER MESSAGE
// ==================================================

function addUserMessage(message) {
    const wrapper = document.createElement("div");

    wrapper.className = "flex justify-end";

    const bubble = document.createElement("div");

    bubble.className =
        "max-w-xl rounded-2xl bg-gray-800 px-4 py-3 whitespace-pre-wrap";

    bubble.textContent = message;

    wrapper.appendChild(bubble);
    messagesContainer.appendChild(wrapper);

    scrollToBottom();
}

// ==================================================
// ASSISTANT MESSAGE
// ==================================================

function createAssistantMessage() {
    const wrapper = document.createElement("div");

    wrapper.className = "flex gap-3";

    wrapper.innerHTML = `
        <div class="min-w-0 flex-1">

            <details open class="activity-section mb-4">
                <summary class="cursor-pointer text-sm text-gray-400 hover:text-gray-200">
                    Agent Activity
                </summary>

                <div class="activity-list mt-3 space-y-1"></div>
            </details>

            <div class="answer-content whitespace-pre-wrap"></div>

            <details class="sources-section mt-4 hidden">
                <summary class="cursor-pointer text-sm text-gray-400 hover:text-gray-200">
                    Sources <span class="source-count"></span>
                </summary>

                <div class="sources-list mt-3 space-y-2"></div>
            </details>

        </div>
    `;

    messagesContainer.appendChild(wrapper);
    //assistant.activitySection.open = false;
    scrollToBottom();
    return {
        activityList: wrapper.querySelector(".activity-list"),
        answer: wrapper.querySelector(".answer-content"),
        sourcesSection: wrapper.querySelector(".sources-section"),
        sourcesList: wrapper.querySelector(".sources-list"),
        sourceCount: wrapper.querySelector(".source-count")
    };
}

// ==================================================
// LABELS
// ==================================================

function agentLabel(name) {
    const labels = {
        supervisor_agent: "Supervisor",
        research_agent: "Research Agent",
        deep_research_agent: "Deep Research Agent",
        arxiv_agent: "ArXiv Agent",
        web_agent: "Web Agent",
        news_agent: "News Agent"
    };

    return labels[name] || name || "Agent";
}

function toolLabel(name) {
    const labels = {
        arxiv_search: "ArXiv Search",
        tavily_web_search: "Tavily Web Search",
        exa_news_search: "Exa News Search",
        crawl_html_page: "HTML Crawler",
        extract_pdf_text: "PDF Reader"
    };

    return labels[name] || name || "Tool";
}

// ==================================================
// ACTIVITY
// ==================================================

function addActivity(assistant, text, level = 0) {
    const row = document.createElement("div");

    row.className = "text-sm text-gray-400";

    row.style.paddingLeft = `${level * 20}px`;

    row.textContent = text;

    assistant.activityList.appendChild(row);

    scrollToBottom();

    return row;
}

// ==================================================
// EVENTS
// ==================================================

function handleActivityEvent(data, assistant) {
    if (!data?.event_type) {
        return;
    }

    const type = data.event_type;
    const agent = agentLabel(data.agent);

    // Agent started
    if (type === "agent_start") {
        addActivity(
            assistant,
            `${agent} — Started`,
            data.agent === "arxiv_agent" ? 1 : 0
        );

        return;
    }

    // Sub-agent query
    if (type === "subagent_query") {
        addActivity(
            assistant,
            `${agent} — Query: ${data.query || ""}`,
            data.agent === "arxiv_agent" ? 1 : 0
        );

        return;
    }

    // Tool started
    if (type === "tool_start") {
        addActivity(
            assistant,
            `${toolLabel(data.tool)} — Started`,
            2
        );

        return;
    }

    // Tool progress
    if (type === "tool_progress") {
        addActivity(
            assistant,
            `${toolLabel(data.tool)} — ${data.message || ""}`,
            2
        );

        return;
    }

    // Tool completed
    if (type === "tool_complete") {
        const count =
            data.result_count !== undefined
                ? ` · ${data.result_count} results`
                : "";

        addActivity(
            assistant,
            `${toolLabel(data.tool)} — Completed${count}`,
            2
        );

        return;
    }

    // Tool error
    if (type === "tool_error") {
        addActivity(
            assistant,
            `${toolLabel(data.tool)} — Error: ${data.message || ""}`,
            2
        );

        return;
    }

    // Agent completed
    if (type === "agent_complete") {
        addActivity(
            assistant,
            `${agent} — Completed`,
            data.agent === "arxiv_agent" ? 1 : 0
        );

        return;
    }

    // Agent error
    if (type === "agent_error") {
        addActivity(
            assistant,
            `${agent} — Error: ${data.message || ""}`,
            data.agent === "arxiv_agent" ? 1 : 0
        );
    }
}


// ==================================================
// SOURCES
// ==================================================

function addSource(assistant, data) {
    const source = data?.source || data;

    if (!source) {
        return;
    }

    assistant.sourcesSection.classList.remove("hidden");

    const item = document.createElement("div");

    item.className =
        "rounded-md border border-gray-800 bg-gray-900 px-3 py-2";

    const title = document.createElement("div");

    title.className =
        "text-sm text-gray-200";

    title.textContent =
        source.title || "Untitled source";

    item.appendChild(title);

    const meta = [];

    if (
        source.author &&
        source.author !== "Not available"
    ) {
        meta.push(source.author);
    }

    if (
        source.published_date &&
        source.published_date !== "Not available"
    ) {
        meta.push(source.published_date);
    }

    if (meta.length) {
        addText(
            item,
            meta.join(" · "),
            "mt-1 text-xs text-gray-500"
        );
    }

    if (source.url) {
        try {
            const url = new URL(source.url);

            if (
                url.protocol === "http:" ||
                url.protocol === "https:"
            ) {
                const link = document.createElement("a");

                link.href = url.href;
                link.target = "_blank";
                link.rel = "noopener noreferrer";

                link.className =
                    "mt-1 inline-block text-xs text-blue-400 hover:underline";

                link.textContent = "Open source";

                item.appendChild(link);
            }
        } catch {
            // Ignore invalid URLs.
        }
    }

    assistant.sourcesList.appendChild(item);

    const count =
        assistant.sourcesList.children.length;

    assistant.sourceCount.textContent =
        ` · ${count}`;

    scrollToBottom();
}

// ==================================================
// SSE STREAM
// ==================================================

async function streamResponse(response, assistant) {
    if (!response.body) {
        throw new Error("Response body is empty");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";

    while (true) {
        const { value, done } = await reader.read();

        if (done) {
            break;
        }

        buffer += decoder.decode(value, {
            stream: true
        });

        const events = buffer.split(/\r?\n\r?\n/);

        buffer = events.pop() || "";

        for (const event of events) {
            for (const line of event.split(/\r?\n/)) {
                if (!line.startsWith("data:")) {
                    continue;
                }

                const json = line
                    .replace(/^data:\s*/, "")
                    .trim();

                if (!json) {
                    continue;
                }

                try {
                    const data = JSON.parse(json);

                    if (data.type === "progress") {
                        handleActivityEvent(
                            data.data,
                            assistant
                        );
                    }

                    else if (data.type === "sources") {
                        addSource(
                            assistant,
                            data.data
                        );
                    }

                    else if (data.type === "token") {
                        assistant.answer._markdown =
                            (assistant.answer._markdown || "") + data.data;

                        const html = renderMarkdown(
                            assistant.answer._markdown
                        );
                        updateAnswer(assistant.answer, html);

                        scrollToBottom();
                    }

                } catch (error) {
                    console.warn(
                        "Invalid SSE event:",
                        error
                    );
                }
            }
        }
    }
}

// ==================================================
// SEND MESSAGE
// ==================================================

async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) {
        return;
    }

    addUserMessage(message);

    messageInput.value = "";
    sendButton.disabled = true;

    const assistant =
        createAssistantMessage();

    try {
        const response = await fetch(
            "/chat/stream",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",
                    "Authorization":
                        `Bearer ${token}`
                },

                body: JSON.stringify({
                    message
                })
            }
        );

        if (!response.ok) {
            // The token is missing, invalid, or expired - clear it and
            // send the user back to the login page.
            if (response.status === 401) {
                localStorage.removeItem("token");
                window.location.replace("/login");
                return;
            }

            throw new Error(
                `Request failed: ${response.status}`
            );
        }

        await streamResponse(
            response,
            assistant
        );

    } catch (error) {
        console.error(
            "Chat stream error:",
            error
        );

        assistant.answer.textContent =
            "Sorry, something went wrong.";

    } finally {
        sendButton.disabled = false;
        messageInput.focus();
    }
}

// ==================================================
// EVENTS
// ==================================================

sendButton.addEventListener(
    "click",
    sendMessage
);

messageInput.addEventListener(
    "keydown",
    (event) => {
        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {
            event.preventDefault();
            sendMessage();
        }
    }
);
// ==================================================
// SESSION INIT: username + logout
// ==================================================

async function initSession() {
    try {
        const response = await fetch(
            "/api/auth/me",
            {
                headers: {
                    "Authorization":
                        `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            localStorage.removeItem("token");
            window.location.replace("/login");
            return;
        }

        const user = await response.json();

        const nameEl = document.getElementById(
            "currentUser"
        );

        if (nameEl) {
            nameEl.textContent = user.username;
        }

    } catch (error) {
        console.error(
            "Session check failed:",
            error
        );
        localStorage.removeItem("token");
        window.location.replace("/login");
    }
}

const logoutBtn = document.getElementById(
    "logoutBtn"
);

if (logoutBtn) {
    logoutBtn.addEventListener(
        "click",
        (event) => {
            event.preventDefault();
            localStorage.removeItem("token");
            window.location.replace("/login");
        }
    );
}

initSession();
