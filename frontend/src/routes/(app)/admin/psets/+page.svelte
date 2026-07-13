<script lang="ts">
    import { goBack } from "$lib/navigationHistory.svelte";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";
    import {csrfFetch, type ProblemSet} from "$lib/utils"

    let psets: ProblemSet[] = $state([]) 

    let name: string = $state("")

    async function getData() {
        const response: Response = await fetch("/api/admin/psets")

        if (!response.ok) {
            await addErrorToast(response, "Failed to load problem set list")
            goBack()
            return
        }

        const data = await response.json()
        psets = data.psets
    }

    async function addPset(event: Event) {
        event.preventDefault()

        const response: Response = await csrfFetch("/api/admin/add/pset", "POST", JSON.stringify({
            name: name
        }))

        if (response.ok) {
            await getData()
            addToast(`Created new problem set ${name}`, ToastType.Success)
        } else {
            await addErrorToast(response, `Failed to create problem set ${name}`)
        }
    }
</script>

<div class="main-container">
    <h1>Problem Sets</h1>
    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#each psets as pset}
            <a href="/admin/pset?id={pset.id}">{pset.name}</a>
            <br>
        {/each}

        <h2>Add Problem Set</h2>
        <form onsubmit={addPset}>
            <label for="name">Name</label>
            <input name="name" type="text" bind:value={name}>
            <input type="submit" value="Add Problem Set">
        </form>
    {/await}
</div>
