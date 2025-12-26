let currentChatId = null;
let isRegister = false;

function switchToRegister() {
    isRegister = true;
    document.getElementById("auth-title").innerText = "Create an Account";
    document.getElementById("auth-btn").innerText = "Register";
    document.getElementById("auth-btn").onclick = register;
    document.querySelector(".auth-switch").innerHTML =
        `Already have an account? <span onclick="switchToLogin()">Login</span>`;
    document.getElementById("auth-msg").innerText = "";
}

function switchToLogin() {
    isRegister = false;
    document.getElementById("auth-title").innerText = "Login to ChitChat";
    document.getElementById("auth-btn").innerText = "Login";
    document.getElementById("auth-btn").onclick = login;
    document.querySelector(".auth-switch").innerHTML =
        `Don’t have an account? <span onclick="switchToRegister()">Register</span>`;
    document.getElementById("auth-msg").innerText = "";
}



// ---------------- AUTH ----------------

function register() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (!email || !password) {
        document.getElementById("auth-msg").innerText = "Please fill all fields";
        return;
    }

    fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            document.getElementById("auth-msg").innerText = data.error;
        } else {
            document.getElementById("auth-msg").innerText =
                "Registered successfully. Please login.";
            switchToLogin();
        }
    })
    .catch(() => {
        document.getElementById("auth-msg").innerText = "Server error";
    });
}


function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (!email || !password) {
        document.getElementById("auth-msg").innerText = "Please fill all fields";
        return;
    }

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.location.href = "/";
        } else {
            document.getElementById("auth-msg").innerText = data.error;
        }
    })
    .catch(() => {
        document.getElementById("auth-msg").innerText = "Server error";
    });
}
// LOAD CHAT LIST
function loadChats() {
    fetch("/chats")
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById("chat-list");
            list.innerHTML = "";
            data.forEach(chat => {
                const div = document.createElement("div");
                div.className = "chat-item";
                div.innerText = chat.title;
                div.onclick = () => openChat(chat.id);
                list.appendChild(div);
            });
        });
}

// OPEN CHAT
function openChat(chatId) {
    currentChatId = chatId;
    document.getElementById("messages").innerHTML = "";

    fetch(`/messages/${chatId}`)
        .then(res => res.json())
        .then(data => {
            data.forEach(m => {
                addMessage(m.content, m.role === "user" ? "user" : "bot");
            });
        });
}

// SEND MESSAGE (NO STREAMING – STABLE)
function sendMessage() {
    const input = document.getElementById("message-input");
    const message = input.value.trim();
    if (!message) return;

    input.value = "";
    addMessage(message, "user");

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            chat_id: currentChatId,
            message: message
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            addMessage(data.error, "bot");
            return;
        }
        currentChatId = data.chat_id;
        addMessage(data.reply, "bot");
        loadChats();
    });
}

// ADD MESSAGE
function addMessage(text, type) {
    const div = document.createElement("div");
    div.className = "message " + type;
    div.innerText = text;
    document.getElementById("messages").appendChild(div);
    scrollBottom();
    return div;
}

// SCROLL
function scrollBottom() {
    const m = document.getElementById("messages");
    m.scrollTop = m.scrollHeight;
}

// ENTER KEY
function handleEnter(e) {
    if (e.key === "Enter") sendMessage();
}

// NEW CHAT (manual only)
function newChat() {
    currentChatId = null;
    document.getElementById("messages").innerHTML = "";
}

// LOAD ON START
loadChats();
