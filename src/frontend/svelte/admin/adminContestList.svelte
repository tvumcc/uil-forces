<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "../components/menuBar.svelte"
    import {getTzOffset} from "../../utils"

    let contests = $state([]) 

    // state for add contest section
    let name = $state()
    let startTime: Date = $state(new Date())
    let endTime: Date = $state(new Date())

    async function getData() {
        let response: Response = await fetch("/api/admin/contests")
        let json = await response.json()
        contests = json["contests"]
    }

    async function addContest(event: Event) {
        event.preventDefault()

        let response = await fetch("/api/admin/add/contest", {
            method: "POST",
            body: JSON.stringify({
                name: name,
                start_time: new Date(startTime + getTzOffset()).toISOString(),
                end_time: new Date(endTime + getTzOffset()).toISOString() 
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
    <h1>Contests</h1>

    {#each contests as contest}
        <a href="/admin/contest?id={contest["id"]}">{contest["name"]}</a>
        <br>
    {/each}

    <h2>Add Contest</h2>
    <form onsubmit={addContest}>
        <label for="name">Name</label>
        <input name="name" type="text" bind:value={name}>
        <label for="start-time">Start Time</label>
        <input name="start-time" type="datetime-local" bind:value={startTime}>
        <label for="end-time">End Time</label>
        <input name="end-time" type="datetime-local" bind:value={endTime}>
        <input type="submit" value="Add Contest">
    </form>
</div>