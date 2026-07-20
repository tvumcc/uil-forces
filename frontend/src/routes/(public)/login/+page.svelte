<script lang="ts">
    import { goto } from "$app/navigation";
    import { page } from "$app/state";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";
    import { csrfFetch } from "$lib/utils"

    let username = $state("")
    let password = $state("")
    let submitting = $state(false)

    async function login(event: Event) {
        event.preventDefault()
        submitting = true

        const response: Response = await csrfFetch("/api/login", "POST", {
            username: username,
            password: password
        })

        if (!response.ok) {
            await addErrorToast(response, "Login failed, please try again")
            submitting = false
            return
        }

        addToast(`Welcome back, ${username}`, ToastType.Success)
        const next = page.url.searchParams.get("next")
        goto(next || "/")
    }
</script>

<div class="main-container narrow">
    <header class="hero centered">
        <h1>UIL Forces</h1>
        <p class="subtitle">Sign in to continue</p>
    </header>

    <form class="stacked-form" onsubmit={login}>
        <div class="field">
            <label for="username">Username</label>
            <input bind:value={username} name="username" type="text" autocomplete="off">
        </div>
        <div class="field">
            <label for="password">Password</label>
            <input bind:value={password} name="password" type="password" autocomplete="off">
        </div>
        <button type="submit" class="btn btn-primary full-width" disabled={submitting}>
            {submitting ? "Logging in…" : "Log In"}
        </button>
        <p class="register-link">
            <a href="/register">Create New Account</a>
        </p>
    </form>
</div>