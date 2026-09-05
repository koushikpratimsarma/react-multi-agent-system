console.log("🔥 CHAT.JS LOADED");

const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");

const messagesContainer = document.querySelector(
    ".mx-auto.max-w-3xl"
);


// ==================================================
// SCROLL
// ==================================================

function scrollToBottom() {
    messagesContainer.parentElement.scrollTop =
        messagesContainer.parentElement.scrollHeight;
}


// ==================================================
// USER MESSAGE
// ==================================================

function addUserMessage(message) {

    const messageDiv = document.createElement("div");

    messageDiv.className = "flex justify-end";

    messageDiv.innerHTML = `
        <div class="max-w-xl rounded-2xl bg-gray-800 px-4 py-3">
            ${message}
        </div>
    `;

    messagesContainer.appendChild(messageDiv);

    scrollToBottom();
}


// ==================================================
// ASSISTANT MESSAGE
// ==================================================

function createAssistantMessage() {

    const assistantDiv =
        document.createElement("div");

    assistantDiv.className =
        "flex gap-3";

    assistantDiv.innerHTML = `
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-700">
            🤖
        </div>

        <div class="assistant-content max-w-xl rounded-2xl bg-gray-900 px-4 py-3">

            <div class="progress-container flex items-center gap-2 text-sm text-gray-500">
                <span class="animate-pulse">●</span>

                <span class="progress-text">
                    Thinking...
                </span>
            </div>

            <div class="answer-content whitespace-pre-wrap"></div>

        </div>
    `;

    messagesContainer.appendChild(
        assistantDiv
    );

    scrollToBottom();


    return {
        assistantDiv,
        progressContainer:
            assistantDiv.querySelector(
                ".progress-container"
            ),
        progressText:
            assistantDiv.querySelector(
                ".progress-text"
            ),
        answerContent:
            assistantDiv.querySelector(
                ".answer-content"
            )
    };
}


// ==================================================
// UPDATE PROGRESS
// ==================================================

function updateProgress(
    progressContainer,
    progressText,
    message
) {

    console.log(
        "🔥 UPDATING UI PROGRESS:",
        message
    );


    progressText.textContent =
        message;


    progressContainer.classList.remove(
        "hidden"
    );


    scrollToBottom();
}


// ==================================================
// REMOVE PROGRESS
// ==================================================

function removeProgress(
    progressContainer
) {

    console.log(
        "🔥 REMOVING UI PROGRESS"
    );


    progressContainer.classList.add(
        "hidden"
    );
}


// ==================================================
// SEND MESSAGE
// ==================================================

async function sendMessage() {

    console.log(
        "🔥 SEND MESSAGE CALLED"
    );


    const message =
        messageInput.value.trim();


    if (!message) {
        return;
    }


    // --------------------------------------------------
    // User message
    // --------------------------------------------------

    addUserMessage(message);

    messageInput.value = "";

    sendButton.disabled = true;


    // --------------------------------------------------
    // Create assistant message
    // --------------------------------------------------

    const {
        progressContainer,
        progressText,
        answerContent
    } = createAssistantMessage();


    try {

        // --------------------------------------------------
        // Request
        // --------------------------------------------------

        const response =
            await fetch(
                "/chat/stream",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        message: message
                    })
                }
            );


        console.log(
            "🔥 RESPONSE RECEIVED:",
            response
        );


        if (!response.ok) {

            throw new Error(
                `Request failed: ${response.status}`
            );
        }


        if (!response.body) {

            throw new Error(
                "Response body is empty"
            );
        }


        // --------------------------------------------------
        // Reader
        // --------------------------------------------------

        const reader =
            response.body.getReader();

        const decoder =
            new TextDecoder();

        let buffer = "";


        // --------------------------------------------------
        // Read stream
        // --------------------------------------------------

        while (true) {

            const {
                value,
                done
            } = await reader.read();


            if (done) {

                console.log(
                    "🔥 STREAM FINISHED"
                );

                break;
            }


            // --------------------------------------------------
            // Decode
            // --------------------------------------------------

            const chunk =
                decoder.decode(
                    value,
                    {
                        stream: true
                    }
                );


            console.log(
                "🔥 RAW CHUNK:",
                chunk
            );


            buffer += chunk;


            // --------------------------------------------------
            // Split SSE events
            // --------------------------------------------------

            const events =
                buffer.split(
                    /\r?\n\r?\n/
                );


            buffer =
                events.pop() || "";


            // --------------------------------------------------
            // Process events
            // --------------------------------------------------

            for (
                const event
                of events
            ) {

                const lines =
                    event.split(
                        /\r?\n/
                    );


                for (
                    const line
                    of lines
                ) {

                    if (
                        !line.startsWith(
                            "data:"
                        )
                    ) {
                        continue;
                    }


                    const jsonString =
                        line
                            .replace(
                                /^data:\s*/,
                                ""
                            )
                            .trim();


                    if (!jsonString) {
                        continue;
                    }


                    try {

                        const data =
                            JSON.parse(
                                jsonString
                            );


                        console.log(
                            "🔥 SSE EVENT:",
                            data
                        );


                        // ==========================================
                        // PROGRESS
                        // ==========================================

                        if (
                            data.type ===
                            "progress"
                        ) {

                            updateProgress(
                                progressContainer,
                                progressText,
                                data.data
                            );
                        }


                        // ==========================================
                        // TOKEN
                        // ==========================================

                        else if (
                            data.type ===
                            "token"
                        ) {

                            console.log(
                                "🔥 TOKEN:",
                                data.data
                            );


                            // Hide progress
                            removeProgress(
                                progressContainer
                            );


                            // Add token
                            answerContent.textContent +=
                                data.data;


                            scrollToBottom();
                        }


                        // ==========================================
                        // FINAL ANSWER
                        // ==========================================

                        else if (
                            data.type ===
                            "answer"
                        ) {

                            console.log(
                                "🔥 ANSWER EVENT:",
                                data.data
                            );


                            // We don't append this
                            // because token events
                            // already constructed
                            // the answer.
                        }

                    }
                    catch (error) {

                        console.error(
                            "❌ JSON PARSE ERROR:",
                            jsonString,
                            error
                        );
                    }
                }
            }
        }


        // --------------------------------------------------
        // Finish
        // --------------------------------------------------

        removeProgress(
            progressContainer
        );

        scrollToBottom();

    }
    catch (error) {

        console.error(
            "❌ STREAM ERROR:",
            error
        );


        removeProgress(
            progressContainer
        );


        answerContent.textContent =
            "Sorry, something went wrong.";
    }
    finally {

        sendButton.disabled = false;

        messageInput.focus();
    }
}


// ==================================================
// SEND BUTTON
// ==================================================

sendButton.addEventListener(
    "click",
    sendMessage
);


// ==================================================
// ENTER KEY
// ==================================================

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