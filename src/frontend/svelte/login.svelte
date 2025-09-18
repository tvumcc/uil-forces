<script lang="ts">
    let username = $state()
    let password = $state()

    async function login(event: Event) {
        event.preventDefault()

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
        let json = await response.json()

        if (response.ok) {
            if (json["login_success"]) {
                window.location.href = json["redirect"]
            }
        }
    }
</script>

<style>
    @import "../style.css";

    .main-container {
        margin-left: 35vw;
        margin-right: 35vw;
        padding-left: 50px;
        padding-right: 50px;
        min-width: fit-content;
        max-width: fit-content;
        min-height: fit-content;
        max-height: fit-content;
    }

    h1 {
        font-size: 40px;
    }

    .form-region {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 25px;
    }

    label {
        font-size: 20px;
    }

    .entry-input {
        font-size: 20px;
        background-color: #0a0f18;
        color: white;
        border: 1px gray solid;
        border-radius: 5px;
        margin-left: 10px;
    }
</style>

<div class="main-container">
    <form onsubmit={login}>
        <div class="form-region">
            <h1>UIL Forces</h1>
        </div>
        <div class="form-region">
            <label for="username">Username:</label>
            <input bind:value={username} name="username" type="text" class="entry-input" autocomplete="off">
        </div>
        <div class="form-region">
            <label for="password">Password:</label>
            <input bind:value={password} name="password" type="password" class="entry-input" autocomplete="off">
        </div>
        <div class="form-region">
            <input value="Log in" type="submit">
        </div>
    </form>
</div>