<script lang="ts">
    import { goBack } from "$lib/navigationHistory.svelte";
    import { addToast, ToastType } from "$lib/toastStore.svelte";
    import {csrfFetch, type Settings} from "$lib/utils"

    let settings: Settings | undefined = $state()

    async function getData() {
        const response: Response = await fetch(`/api/admin/settings`)
        const data = await response.json()

        if (!response.ok) {
            addToast("Failed to retreive settings", ToastType.Error)
            goBack()
            return
        }        

        settings = data.settings
    }

    async function editSettings(event: Event) {
        event.preventDefault()

        const response: Response = await csrfFetch("/api/admin/update/settings", "POST", JSON.stringify({
            docker_grading: settings!.docker_grading
        }))

        if (response.ok) {
            await getData()
            addToast("Updated settings")
        } else {
            addToast("Failed to update settings")
        }
    }
</script>

<div class="main-container">
    <h1>Site-wide Settings</h1>

    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if settings !== undefined} 
            <form onsubmit={editSettings}>
                <table>
                    <tbody>
                        <tr>
                            <td><label for="docker-grading">Use Docker Grading</label></td>
                            <td><input name="docker-grading" type="checkbox" bind:checked={settings.docker_grading}></td>
                        </tr>
                    </tbody>
                </table>
                <input type="submit" value="Update Settings">
            </form>
        {/if}
    {/await}

</div>

<style>
    table {
        border-collapse: collapse;
    }

    td {
        border: 1px gray solid;
        margin: 0;
        padding: 8px;
        text-align: left;
    }
</style>