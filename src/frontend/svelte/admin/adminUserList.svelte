<script lang="ts">
    import MenuBar from "../components/menuBar.svelte"
    import type {User} from "../../utils"

    let validRequest = $state(true)
    let message = $state("")

    let users: User[] = $state([])

    // state for add user section
    let username = $state("")
    let password = $state("")
    let isAdmin = $state(false)

    async function getData() {
        let response: Response = await fetch("/api/admin/users")
        let json = await response.json()

        if (!response.ok) {
            validRequest = false
            message = json.description
        }

        users = json.users
    }

    async function addUser(event: Event) {
        event.preventDefault()

        let response = await fetch("/api/admin/add/user", {
            method: "POST",
            body: JSON.stringify({
                username: username,
                password: password,
                isAdmin: isAdmin
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok) {
            await getData()
        }
    }
</script>

<style>
    @import "../../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Users</h1>

    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if validRequest} 
            {#each users as user}
                <a href="/user?id={user["id"]}">{user.username} {user.isAdmin ? "(admin)" : ""}</a>
                <p>Password: {user.password}</p>
                <br>
            {/each}

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

        {:else}
            <p>{message}</p>
        {/if}
    {/await}
</div>