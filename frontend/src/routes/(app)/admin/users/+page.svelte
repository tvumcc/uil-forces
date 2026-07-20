<script lang="ts">
    import { onMount } from "svelte";
    import { csrfFetch, type User } from "$lib/utils"
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte"
    import { goBack } from "$lib/navigationHistory.svelte";

    let users: User[] | undefined = $state([])
    let loading = $state(true)

    let username = $state("")
    let password = $state("")
    let isAdmin = $state(false)

    async function getData() {
        const response: Response = await fetch("/api/admin/users")
        if (!response.ok) {
            await addErrorToast(response, "Failed to load user list")
            goBack()
            return
        }
        const data = await response.json()
        users = data.users
        loading = false
    }

    async function addUser(event: Event) {
        event.preventDefault()
        let response = await csrfFetch("/api/admin/user/add", "POST", {
            username: username,
            password: password,
            isAdmin: isAdmin
        })
        if (response.ok) {
            await getData()
            addToast(`Created user ${username}`, ToastType.Success)
            username = ""
            password = ""
            isAdmin = false
        } else {
            await addErrorToast(response, "Failed to create user")
        }
    }

    onMount(() => {
        getData()
    })
</script>

<div class="main-container">
    <header class="hero">
        <h1>Users</h1>
    </header>

    {#if loading}
        <div class="panel skeleton"></div>
    {:else}
        <section class="panel">
            <h2 class="section-header">All Users</h2>
            {#if users !== undefined && users.length > 0}
                <ul class="contest-list">
                    {#each users as user}
                        <li>
                            <span>{user.username}</span>
                            {#if user.isAdmin}
                                <span class="badge badge-admin">Admin</span>
                            {/if}
                        </li>
                    {/each}
                </ul>
            {:else}
                <p class="empty-state">No users found.</p>
            {/if}
        </section>

        <section class="panel spaced">
            <h2 class="section-header">Create New User</h2>
            <form class="stacked-form" onsubmit={addUser}>
                <div class="field">
                    <label for="username">Username</label>
                    <input name="username" type="text" bind:value={username}>
                </div>
                <div class="field">
                    <label for="password">Password</label>
                    <input name="password" type="password" bind:value={password}>
                </div>
                <div class="checkbox-row">
                    <label class="checkbox-field">
                        <input name="is_admin" type="checkbox" bind:checked={isAdmin}>
                        Give Admin Privileges
                    </label>
                </div>
                <button type="submit" class="btn btn-primary">Create User</button>
            </form>
        </section>
    {/if}
</div>