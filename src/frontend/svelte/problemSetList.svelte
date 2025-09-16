<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "./components/menubar.svelte"

    let psets = $state([])

    async function getData() {
        let response: Response = await fetch("/api/psets")
        let json = await response.json()
        psets = json["psets"]
    }

    onMount(getData)
</script>

<style>
    @import "../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Problem Sets</h1>

    {#if psets.length > 0}
        {#each psets as pset}
            <a href="/pset?id={pset["id"]}">{pset["name"]}</a><br>
        {/each}
    {/if}
</div>