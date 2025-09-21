<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "./components/menubar.svelte"

    let users = $state([])

    // state for add user section
    let username = $state("")
    let password = $state("")
    let is_admin = $state(false)

    async function getData() {
        let response: Response = await fetch("/api/admin/users")
        let json = await response.json()
        users = json["users"]
    }

    async function addUser(event: Event) {
        event.preventDefault()
        console.log(is_admin)

        let response = await fetch("/api/admin/add/user", {
            method: "POST",
            body: JSON.stringify({
                username: username,
                password: password,
                is_admin: is_admin
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok) {
            await getData()
        }
    }

    $effect(() => {
        console.log(is_admin)
    })

    onMount(getData)
</script>

<style>
    @import "../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Users</h1>
    {#each users as user}
        <a href="/user?id={user["id"]}">{user["username"]} {user["is_admin"] ? "(admin)" : ""}</a>
        <p>Password: {user["passphrase"]}</p>
        <br>
    {/each}

    <h2>Add User</h2>
    <form onsubmit={addUser}>
        <label for="username">Username</label>
        <input name="username" type="text" bind:value={username}>
        <label for="passphrase">Password</label>
        <input name="passphrase" type="text" bind:value={password}>
        <label for="is_admin">Admin</label>
        <input name="is_admin" type="checkbox" bind:checked={is_admin}>
        <input type="submit" value="Add User">
    </form>
</div>