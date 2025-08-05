<script lang="ts">
    let username = $state()
    let password = $state()

    async function login() {
        let response = await fetch("/api/login", {
            method: "POST",
            body: JSON.stringify({
                username: username,
                password: password
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })
        let response_json = await response.json()

        if (response.ok) {
            if (response_json["login_success"]) {
                window.location.href = response_json["redirect"]
            }
        }
    }
</script>

<h1>Login Page</h1>
<p>Username:</p>
<input bind:value={username} type="text">
<p>Password:</p>
<input bind:value={password} type="password">
<button onclick={login}>Log in</button>