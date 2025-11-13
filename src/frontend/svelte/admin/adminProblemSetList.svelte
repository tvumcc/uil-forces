<script lang="ts">
    import MenuBar from "../components/menuBar.svelte"
    import type {ProblemSet} from "../../utils"

    let validRequest = $state(true)
    let message = $state("")

    let psets: ProblemSet[] = $state([]) 

    // state for add pset section
    let name = $state()

    let files: FileList = $state()!
    let fileData: ArrayBuffer = $state(new ArrayBuffer(0))

    async function getData() {
        let response: Response = await fetch("/api/admin/psets")
        let json = await response.json()

        if (!response.ok) {
            validRequest = false
            message = json.description
        }

        psets = json.psets
    }

    async function addPset(event: Event) {
        event.preventDefault()

        let response = await fetch("/api/admin/add/pset", {
            method: "POST",
            body: JSON.stringify({
                name: name
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok) {
            await getData()
        }
    }

    async function importPsets(event: Event) {
        event.preventDefault()

        let formData = new FormData()
        formData.append("psets", new Blob([fileData], { type: "application/zip" }), "psets.zip")

        let response: Response = await fetch(`/api/admin/psets/import`, {
            method: "POST",
            body: formData
        })

        if (response.ok) {
            await getData()
        }
    }

    $effect(() => {
        (async () => {
            if (files) {
                for (let file of files) {
                    fileData = await file.arrayBuffer()
                }
            }
        })()
    })
</script>

<style>
    @import "../../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Problem Sets</h1>
    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if validRequest}
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

            <h2>Import Problem Sets</h2>
            <form onsubmit={importPsets}>
                <input name="import-psets" type="file" bind:files>
                <input type="submit" value="Import Problem Sets">
            </form>

            <a href="/api/admin/psets/export" target="_blank">Export Problem Sets</a>
        {:else}
            <p>{message}</p>
        {/if}
    {/await}
</div>