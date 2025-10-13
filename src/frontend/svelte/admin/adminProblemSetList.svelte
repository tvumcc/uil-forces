<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "../components/menuBar.svelte"

    let psets = $state([]) 

    // state for add pset section
    let name = $state()
    let startTime: Date = $state(new Date())
    let endTime: Date = $state(new Date())

    async function getData() {
        let response: Response = await fetch("/api/admin/psets")
        let json = await response.json()
        psets = json["psets"]
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

    onMount(getData)
</script>

<style>
    @import "../../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Problem Sets</h1>

    {#each psets as pset}
        <a href="/admin/pset?id={pset["id"]}">{pset["name"]}</a>
        <br>
    {/each}

    <h2>Add Problem Set</h2>
    <form onsubmit={addPset}>
        <label for="name">Name</label>
        <input name="name" type="text" bind:value={name}>
        <input type="submit" value="Add Problem Set">
    </form>
</div>