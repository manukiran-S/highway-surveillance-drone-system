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
});
