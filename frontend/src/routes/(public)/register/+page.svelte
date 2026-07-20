<script lang="ts">
    import { goto } from "$app/navigation";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte"
    import { csrfFetch } from "$lib/utils";

    let username = $state("")
    let password = $state("")
    let submitting = $state(false)

    async function register(event: Event) {
        event.preventDefault()
        submitting = true

        const response: Response = await csrfFetch("/api/register", "POST", {
            username: username,
            password: password
        })

        if (!response.ok) {
            await addErrorToast(response, "User registration failed, please try again")
            submitting = false
            return
        }

        addToast(`Welcome, ${username}`, ToastType.Success)
        goto("/")
    }
</script>

<div class="main-container narrow">
    <header class="hero centered">
        <h1>UIL Forces</h1>
        <p class="subtitle">Create a new account</p>
    </header>

    <form class="stacked-form" onsubmit={register}>
        <div class="field">
            <label for="username">Username</label>
            <input bind:value={username} name="username" type="text" autocomplete="off">
        </div>
        <div class="field">
            <label for="password">Password</label>
            <input bind:value={password} name="password" type="password" autocomplete="off">
        </div>
        <button type="submit" class="btn btn-primary full-width" disabled={submitting}>
            {submitting ? "Creating account…" : "Create New Account"}
        </button>
        <p class="register-link">
            <a href="/login">Log in to an existing account</a>
        </p>
    </form>
</div>