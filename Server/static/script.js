const socket = io.connect("http://192.168.196.52:5000");

socket.on("connect", () => {
  console.log("Connected to WebSocket server.");
  socket.emit("join", { room: "game_room_1", username: "Player1" });
});

socket.on("game_update", (data) => {
  console.log("Game update:", data);
  updateGameUI(data);
});

socket.on("message", (data) => {
  console.log(data.msg);
});

function sendAction(action, amount = 0) {
  socket.emit("action", {
    room: "game_room_1",
    action: action,
    amount: amount,
  });
}

function updateGameUI(data) {
  const potElement = document.getElementById("pot");
  const betsElement = document.getElementById("bets");
  const cardsElement = document.getElementById("community-cards");

  potElement.textContent = `Pot: ${data.pot}`;
  betsElement.innerHTML = Object.entries(data.bets)
    .map(([player, bet]) => `${player}: ${bet}`)
    .join("<br>");

  cardsElement.textContent = `Cards: ${data.community_cards.join(", ")}`;
}

async function login(event) {
  event.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: username, password: password }),
  });

  const result = await response.json();
  if (response.ok) {
    alert(result.message);
    localStorage.setItem("token", result.token);
    localStorage.setItem("username", username); // Store username in localStorage
    window.location.href = "/main_page";
  } else {
    alert(result.error + " başarısız giriş denemesi");
    window.location.href = "/";
  }
}

async function register(event) {
  event.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email, password: password }),
  });

  const result = await response.json();
  if (response.ok) {
    alert(result.message);
    window.location.href = "/login.html";
  } else {
    alert(result.error);
    window.location.href = "/register.html";
  }
}
