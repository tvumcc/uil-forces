<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "../components/menuBar.svelte"
    import { toTzIsoString, getTzOffset } from "../../utils"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let name = $state("")
    let startTime = $state("")
    let endTime = $state("")
    let allowed_languages = $state([])
    let show_leaderboard = $state(false)
    let show_pdf = $state(false)
    let problems = $state([])

    let psetName = $state("")
    let problemPsetName = $state("")
    let problemName = $state("")

    async function getData() {
        let response: Response = await fetch(`/api/admin/contest/${ID}`)
        let json = await response.json()
        name = json["contest"]["name"]
        startTime = toTzIsoString(new Date(json["contest"]["start_time"]))
        endTime = toTzIsoString(new Date(json["contest"]["end_time"]))
        allowed_languages = json["contest"]["allowed_languages"]
        show_leaderboard = json["contest"]["show_leaderboard"]
        show_pdf = json["contest"]["show_pdf"]
        problems = json["contest"]["problems"]
    }

    async function editContest(event: Event) {
        event.preventDefault()

        console.log(allowed_languages)
        let response: Response = await fetch("/api/admin/update/contest", {
            method: "POST",
            body: JSON.stringify({
                id: ID,
                name: name,
                start_time: new Date(startTime + getTzOffset()).toISOString(),
                end_time: new Date(endTime + getTzOffset()).toISOString(),
                show_pdf: show_pdf,
                show_leaderboard: show_leaderboard,
                allowed_languages: allowed_languages
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok) {
            await getData()
        }
    }

    async function addProblemSet(event: Event) {
        event.preventDefault()

        let response: Response = await fetch(`/api/admin/contest/${ID}/add/pset`, {
            method: "POST",
            body: JSON.stringify({
                pset_name: psetName,
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok) {
            await getData()
        }
    }

    async function addProblem(event: Event) {
        event.preventDefault()

        let response: Response = await fetch(`/api/admin/contest/${ID}/add/problem`, {
            method: "POST",
            body: JSON.stringify({
                pset_name: problemPsetName,
                problem_name: problemName 
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok) {
            await getData()
        }
    }

    async function unlinkProblem(problem_id: number) {
        let response: Response = await fetch("/api/admin/contest/unlinkproblem", {
            method: "POST",
            body: JSON.stringify({
                contest_id: ID,
                problem_id: problem_id
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok)  {
            await getData()
        }
    }

    onMount(getData)
</script>

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
    <h1>Edit Contest</h1>

    <form onsubmit={editContest}>
        <label for="name">Name</label>
        <input name="name" type="text" bind:value={name}>
        <label for="start-time">Start Time</label>
        <input name="start-time" type="datetime-local" bind:value={startTime}>
        <label for="end-time">End Time</label>
        <input name="end-time" type="datetime-local" bind:value={endTime}>
        <br>
        <label for="show-pdf">Show PDF Problem Statement Viewer</label>
        <input name="show-pdf" type="checkbox" bind:checked={show_pdf}>
        <br>
        <label for="show-leaderboard">Show Leaderboard</label>
        <input name="show-leaderboard" type="checkbox" bind:checked={show_leaderboard}>
        <br>
        <label for="allowed-languages">Allowed Languages (space separated)</label>
        <input name="allowed-languages" type="text" bind:value={allowed_languages}>
        <br>
        <input type="submit" value="Update Contest">
    </form>

    <h2>Problems:</h2>
    <table>
    <tbody>
    {#each problems as problem}
        <tr class="pb-row">
            <td><a href="/admin/problem?id={problem["id"]}">{problem["name"]}</a></td>
            <td><button onclick={async ()=>{await unlinkProblem(problem["id"])}}>Remove</button></td>
        </tr>
    {/each}
    </tbody>
    </table>

    <h2>Add Problem Set</h2>
    <form onsubmit={addProblemSet}>
        <label for="pset-name">Problem Set Name</label>
        <input name="pset-name" type="text" bind:value={psetName}>
        <input type="submit" value="Add Problem Set">
    </form>

    <h2>Add Problem</h2>
    <form onsubmit={addProblem}>
        <label for="problem-pset-name">Problem Set Name</label>
        <input name="problem-pset-name" type="text" bind:value={problemPsetName}>
        <label for="problem-name">Problem Name</label>
        <input name="problem-name" type="text" bind:value={problemName}>
        <input type="submit" value="Add Problem">
    </form>
</div>