<script lang="ts">
    import { goto } from "$app/navigation";
    import { addToast, ToastType } from "$lib/toastStore.svelte"
    import { csrfFetch, type User } from "$lib/utils";

    let username = $state()
    let password = $state()

    async function register(event: Event) {
        event.preventDefault()

        let response = await csrfFetch("/api/register", "POST", JSON.stringify({
            username: username,
            password: password
        }))

        if (!response.ok) {
            const err = await response.json().catch(() => ({}))
            addToast(err.error === "user_exists" ? "A user with that username already exists" : "User registration failed, please try again.", ToastType.Error)
            return
        }

        const user: User = await response.json()
        addToast(`Welcome, ${user.username}`)

        goto("/")
    }
</script>

<div class="main-container">
    <form onsubmit={register}>
        <div class="form-region">
            <h1>UIL Forces</h1>
        </div>
        <div class="form-region">
            <h2>Account Creation</h2>
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
            <input value="Create New Account" type="submit">
        </div>
        <div class="form-region">
            <a href="/login">Log in to an existing account</a>
        </div>
    </form>
</div>

<style>
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
