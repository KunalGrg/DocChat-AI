let currentDocumentText = "";

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const fileInfo = document.getElementById("fileInfo");
const fileNameSpan = document.getElementById("fileName");
const textPreview = document.getElementById("textPreview");
const togglePreviewBtn = document.getElementById("togglePreviewBtn");

const chatWindow = document.getElementById("chatWindow");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");

// Drag & Drop
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
        handleFile(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener("change", (e) => {
    if (e.target.files.length) {
        handleFile(e.target.files[0]);
    }
});

async function handleFile(file) {
    // UI Loading state
    fileInfo.classList.remove("hidden");
    fileNameSpan.innerText = "Analyzing " + file.name + "...";
    document.querySelector(".status-badge").innerText = "Processing...";
    document.querySelector(".status-badge").style.color = "#fbbf24"; // Amber

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/api/extract", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const data = await response.json();
        currentDocumentText = data.text;
        
        // Success UI
        fileNameSpan.innerText = data.filename;
        document.querySelector(".status-badge").innerText = "Ready";
        document.querySelector(".status-badge").style.color = "#10b981"; // Green
        
        togglePreviewBtn.disabled = false;
        textPreview.innerText = data.text.substring(0, 1000) + (data.text.length > 1000 ? "..." : "");
        
        addBotMessage(`I've analyzed <strong>${data.filename}</strong>. It contains ${data.text.length} characters. Ask me anything about it!`);

    } catch (error) {
        console.error(error);
        fileNameSpan.innerText = "Error";
        document.querySelector(".status-badge").innerText = "Failed";
        document.querySelector(".status-badge").style.color = "#ef4444"; // Red
        alert("Upload failed: " + error.message);
    }
}

// Preview Toggle
togglePreviewBtn.addEventListener("click", () => {
    textPreview.classList.toggle("hidden");
    togglePreviewBtn.innerText = textPreview.classList.contains("hidden") 
        ? "View Extracted Text" 
        : "Hide Extracted Text";
});

// Chat Logic
sendBtn.addEventListener("click", sendMessage);
questionInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const question = questionInput.value.trim();
    if (!question) return;

    if (!currentDocumentText) {
        addBotMessage("Please upload a document first!");
        return;
    }

    // Add User Message
    addUserMessage(question);
    questionInput.value = "";
    
    // Show Loading in Chat
    const loadingId = addBotMessage("Thinking...", true);

    try {
        const response = await fetch("/api/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                document_text: currentDocumentText,
                question: question
            })
        });

        const data = await response.json();
        
        // Remove loading message and add actual response
        removeMessage(loadingId);
        addBotMessage(data.answer);

    } catch (error) {
        removeMessage(loadingId);
        addBotMessage("Sorry, something went wrong requesting the answer.");
        console.error(error);
    }
}

function addUserMessage(text) {
    const div = document.createElement("div");
    div.className = "message user-message";
    div.innerText = text;
    chatWindow.appendChild(div);
    scrollToBottom();
}

function addBotMessage(text, isLoading = false) {
    const div = document.createElement("div");
    div.className = "message bot-message";
    div.innerHTML = text; // Allow HTML for bolding filename
    if (isLoading) {
        div.id = "msg-" + Date.now();
        div.style.opacity = "0.7";
    }
    chatWindow.appendChild(div);
    scrollToBottom();
    return div.id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}
