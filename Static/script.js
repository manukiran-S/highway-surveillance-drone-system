document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;

            fetch("/authenticate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.redirect) {
                        window.location.href = data.redirect;
                    } else {
                        document.getElementById("error-message").innerText =
                            data.error || "Login failed. Please try again.";
                    }
                })
                .catch(error => {
                    document.getElementById("error-message").innerText =
                        "Login failed. Please try again.";
                    console.error("Login Error:", error);
                });
        });
    }

    function updateDroneStatus() {
        fetch('/drone_status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('battery').textContent = data.battery + '%';
                document.getElementById('vehicleCount').textContent = data.vehicle_count;

                if (data.vehicle_count > 5) {
                    document.getElementById('trafficAlert').textContent = "🚦 Heavy Traffic Detected!";
                    document.getElementById('trafficAlert').style.color = "red";
                } else {
                    document.getElementById('trafficAlert').textContent = "";
                }
            })
            .catch(error => console.error('Error fetching drone status:', error));
    }

    setInterval(updateDroneStatus, 3000);

    // Send drone command
    window.sendCommand = function (cmd) {
        fetch('/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cmd })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(`Error: ${data.error}`);
                } else {
                    console.log(`Command "${cmd}" sent successfully`);
                }
            })
            .catch(error => {
                console.error(`Failed to send "${cmd}" command:`, error);
                alert(`Failed to send "${cmd}" command`);
            });
    };

    // Keyboard controls
    document.addEventListener("keydown", function (e) {
        switch (e.key) {
            case "ArrowUp":
            case "w":
            case "W":
                sendCommand("forward");
                break;
            case "ArrowDown":
            case "s":
            case "S":
                sendCommand("backward");
                break;
            case "ArrowLeft":
            case "a":
            case "A":
                sendCommand("left");
                break;
            case "ArrowRight":
            case "d":
            case "D":
                sendCommand("right");
                break;
            case " ":
                sendCommand("takeoff");
                break;
            case "Shift":
                sendCommand("land");
                break;
            case "q":
            case "Q":
                sendCommand("up");
                break;
            case "e":
            case "E":
                sendCommand("down");
                break;
            case "z":
            case "Z":
                sendCommand("rotate_right");
                break;
            case "x":
            case "X":
                sendCommand("rotate_left");
                break;
        }
    });
});
