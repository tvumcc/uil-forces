<script lang="ts">
    import MenuBar from "../components/menuBar.svelte"
    import type {ProblemSet} from "../../utils"

    let validRequest = $state(true)
    let message = $state("")

    let hide = $state()
    let psets: ProblemSet[] = $state([])

    async function getData() {
        let response: Response = await fetch("/api/psets")
        let json = await response.json()

        hide = json.hide
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
        {#if validRequest}
            {#if hide !== null && hide}
                <p>The practice site has been disabled.</p>
            {:else}
                {#if psets.length > 0}
                    {#each psets as pset}
                        <a href="/pset?id={pset["id"]}">{pset["name"]}</a><br>
                    {/each}
                {/if}
            {/if}
        {:else}
            <p>{message}</p>
        {/if}
    {/await}
</div>