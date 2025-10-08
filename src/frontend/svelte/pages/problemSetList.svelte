<script lang="ts">
    import MenuBar from "../components/menuBar.svelte"

    let psets = $state([])

    async function getData() {
        let response: Response = await fetch("/api/psets")
        let json = await response.json()
        psets = json.psets
    }
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
        {#if psets.length > 0}
            {#each psets as pset}
                <a href="/pset?id={pset["id"]}">{pset["name"]}</a><br>
            {/each}
        {/if}
    {/await}
</div>