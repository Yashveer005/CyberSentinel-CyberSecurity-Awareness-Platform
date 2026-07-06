function checkPassword() {
    let password = document.getElementById("passwordInput").value;
    let strengthBar = document.getElementById("strengthBar");
    let strengthText = document.getElementById("strengthText");

    let strength = 0;

    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[!@#$%^&*]/.test(password)) strength++;

    if (strength === 0) {
        strengthBar.style.width = "0%";
        strengthText.innerText = "";
    }
    else if (strength === 1) {
        strengthBar.style.width = "25%";
        strengthBar.style.background = "red";
        strengthText.innerText = "Weak Password ❌";
    }
    else if (strength === 2) {
        strengthBar.style.width = "50%";
        strengthBar.style.background = "orange";
        strengthText.innerText = "Moderate Password ⚠";
    }
    else if (strength === 3) {
        strengthBar.style.width = "75%";
        strengthBar.style.background = "#00bfff";
        strengthText.innerText = "Good Password 👍";
    }
    else {
        strengthBar.style.width = "100%";
        strengthBar.style.background = "limegreen";
        strengthText.innerText = "Strong Password 🔥";
    }
}

//phishing
document.addEventListener("DOMContentLoaded", function() {

    // ===== PHISHING RISK BAR =====
    const riskBar = document.querySelector(".risk-progress");

    if (riskBar) {
        let score = parseInt(riskBar.getAttribute("data-score")) || 0;
        let percent = score * 20;
        riskBar.style.width = percent + "%";
    }

});

// MATRIX EFFECT SAFE VERSION

const canvas = document.getElementById("matrixCanvas");

if (canvas) {

    const ctx = canvas.getContext("2d");

    canvas.height = window.innerHeight;
    canvas.width = window.innerWidth;

    const letters = "010101010101010101";
    const fontSize = 14;
    const columns = canvas.width / fontSize;

    const drops = [];

    for (let x = 0; x < columns; x++) {
        drops[x] = 1;
    }

    function draw() {
        ctx.fillStyle = "rgba(10, 15, 44, 0.05)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = "#00ff99";
        ctx.font = fontSize + "px monospace";

        for (let i = 0; i < drops.length; i++) {
            const text = letters[Math.floor(Math.random() * letters.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);

            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }

            drops[i]++;
        }
    }

    setInterval(draw, 50);

    window.addEventListener("resize", () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// ==========================
// Password Generator
// ==========================

const generateBtn = document.getElementById("generateBtn");
const copyBtn = document.getElementById("copyBtn");
const passwordField = document.getElementById("generatedPassword");

if(generateBtn){

generateBtn.addEventListener("click", function(){

let chars = "";

if(document.getElementById("uppercase").checked)
    chars += "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

if(document.getElementById("lowercase").checked)
    chars += "abcdefghijklmnopqrstuvwxyz";

if(document.getElementById("numbers").checked)
    chars += "0123456789";

if(document.getElementById("symbols").checked)
    chars += "!@#$%^&*()_+";

if(chars === ""){
    alert("Please select at least one character type.");
    return;
}
const length = document.getElementById("length").value;

let password = "";

for(let i = 0; i < length; i++){

    password += chars.charAt(
        Math.floor(Math.random() * chars.length)
    );

}

passwordField.value = password;

});

}
const slider = document.getElementById("length");
const lengthValue = document.getElementById("lengthValue");

if(slider){

    slider.oninput = function(){

        lengthValue.innerHTML = this.value;

    };

}
if(copyBtn){

copyBtn.addEventListener("click", function(){

passwordField.select();

document.execCommand("copy");

alert("Password Copied!");

});

}
