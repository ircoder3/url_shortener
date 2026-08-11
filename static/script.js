const form = document.getElementById("shorten-form");
const urlInput = document.getElementById("url-input");
const customCodeInput = document.getElementById("custom-code-input");
const resultBox = document.getElementById("result");
const errorBox = document.getElementById("error");
const shortUrlLink = document.getElementById("short-url-link");
const statsLink = document.getElementById("stats-link");
const copyBtn = document.getElementById("copy-btn");
const qrCode = document.getElementById("qr-code");

// History elements
const historyContainer = document.getElementById("history-container");
const historyList = document.getElementById("history-list");

// Load history on page load
document.addEventListener("DOMContentLoaded", renderHistory);

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  
  // Reset UI
  errorBox.classList.add("hidden");
  resultBox.classList.add("hidden");
  qrCode.classList.add("hidden");
  
  const button = form.querySelector("button");
  const originalText = button.textContent;
  button.textContent = "Shortening...";
  button.disabled = true;

  const url = urlInput.value.trim();
  const customCode = customCodeInput.value.trim();

  try {
    const res = await fetch("/shorten", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, custom_code: customCode })
    });

    const data = await res.json();

    if (!res.ok) {
      errorBox.textContent = data.error || "Something went wrong";
      errorBox.classList.remove("hidden");
      return;
    }

    // Update Result UI
    shortUrlLink.textContent = data.short_url;
    shortUrlLink.href = data.short_url;
    statsLink.href = `/${data.short_code}/stats`;
    
    // Generate QR Code via free API
    qrCode.src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(data.short_url)}`;
    qrCode.onload = () => qrCode.classList.remove("hidden");

    resultBox.classList.remove("hidden");

    // Save to local storage history
    saveToHistory(url, data.short_url);
    
    // Clear inputs
    urlInput.value = "";
    customCodeInput.value = "";
    
  } catch (err) {
    errorBox.textContent = "Network error. Please try again.";
    errorBox.classList.remove("hidden");
  } finally {
    button.textContent = originalText;
    button.disabled = false;
  }
});

copyBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(shortUrlLink.textContent).then(() => {
    copyBtn.textContent = "Copied! ✓";
    setTimeout(() => (copyBtn.textContent = "Copy"), 2000);
  });
});

// History Management
function saveToHistory(original, short) {
  let history = JSON.parse(localStorage.getItem("urlHistory")) || [];
  
  // Prevent exact duplicates in history
  if (!history.find(item => item.short === short)) {
    // Keep only last 5 entries
    history.unshift({ original, short });
    if (history.length > 5) history.pop();
    
    localStorage.setItem("urlHistory", JSON.stringify(history));
    renderHistory();
  }
}

function renderHistory() {
  const history = JSON.parse(localStorage.getItem("urlHistory")) || [];
  
  if (history.length === 0) {
    historyContainer.classList.add("hidden");
    return;
  }

  historyContainer.classList.remove("hidden");
  historyList.innerHTML = "";

  history.forEach(item => {
    const li = document.createElement("li");
    
    const linkObj = document.createElement("a");
    linkObj.href = item.short;
    linkObj.target = "_blank";
    linkObj.textContent = item.short.replace(/^https?:\/\//, ''); // Clean display
    
    const hintText = document.createElement("span");
    hintText.className = "original-url-hint";
    hintText.textContent = item.original;

    li.appendChild(linkObj);
    li.appendChild(hintText);
    historyList.appendChild(li);
  });
}