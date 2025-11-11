<script lang="ts">
    import MenuBar from "../components/menuBar.svelte"
    import type {Settings} from "../../utils"

    let validRequest = $state(true)
    let message = $state("")

    let settings: Settings | undefined = $state()

    async function getData() {
        let response: Response = await fetch(`/api/admin/settings`)
        let json = await response.json()

        if (!response.ok) {
            validRequest = false
            message = json.description
        }        

        settings = json.settings
    }

    async function editSettings(event: Event) {
        event.preventDefault()

        let response: Response = await fetch("/api/admin/update/settings", {
            method: "POST",
            body: JSON.stringify({
                practice_site: settings!.practice_site,
                docker_grading: settings!.docker_grading
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

<!-- svelte-ignore css_unused_selector -->
<style>
    @import "../../style.css";

    table {
        border-collapse: collapse;
    }

    .pb-row td {
        border: 1px gray solid;
        margin: 0;
        padding: 8px;
        text-align: left;
    }
</style>

<MenuBar />
<div class="main-container">
    <h1>Site-wide Settings</h1>

    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if validRequest && settings !== undefined} 
            <form onsubmit={editSettings}>
                <label for="practice-site">Enable Practice</label>
                <input name="practice-site" type="checkbox" bind:checked={settings.practice_site}>
                <br>
                <label for="docker-grading">Use Docker Grading</label>
                <input name="docker-grading" type="checkbox" bind:checked={settings.docker_grading}>
                <br>
                <input type="submit" value="Update Settings">
            </form>
        {:else}
            <p>{message}</p>
        {/if}
    {/await}

</div>
