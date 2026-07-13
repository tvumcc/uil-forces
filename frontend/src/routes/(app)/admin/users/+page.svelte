<script lang="ts">
    import {csrfFetch, type User} from "$lib/utils"
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte"
    import { goBack } from "$lib/navigationHistory.svelte";

    let users: User[] | undefined = $state([])

    // state for add user section
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
    }

    async function addUser(event: Event) {
        event.preventDefault()

        let response = await csrfFetch("/api/admin/add/user", "POST", JSON.stringify({
            username: username,
            password: password,
            isAdmin: isAdmin
        }))

        if (response.ok) {
            await getData()
            addToast(`Created user ${username}`, ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to create user")
        }
    }
</script>

<div class="main-container">
    <h1>Users</h1>

    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if users !== undefined}
            {#each users as user}
                <a href="/user?id={user["id"]}">{user.username} {user.isAdmin ? "(admin)" : ""}</a>
                <br>
            {/each}
        {:else}
            <p>User list could not be loaded</p>
        {/if}

        <h2>Add User</h2>
        <form onsubmit={addUser}>
            <label for="username">Username</label>
            <input name="username" type="text" bind:value={username}>
            <label for="password">Password</label>
            <input name="password" type="text" bind:value={password}>
            <label for="is_admin">Admin</label>
            <input name="is_admin" type="checkbox" bind:checked={isAdmin}>
            <input type="submit" value="Add User">
        </form>
    {/await}
</div>
