<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "../components/menuBar.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let name = $state("")
    let hide = $state(true)
    let problems = $state([])

    let problemName = $state("")

    async function getData() {
        let response: Response = await fetch(`/api/admin/pset/${ID}`)
        let json = await response.json()
        name = json["pset"]["name"]
        hide = json["pset"]["hide"]
        problems = json["pset"]["problems"]
    }

    async function editPset(event: Event) {
        event.preventDefault()

        let response: Response = await fetch("/api/admin/update/pset", {
            method: "POST",
            body: JSON.stringify({
                id: ID,
                name: name,
                hide: hide
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

        let response: Response = await fetch(`/api/admin/pset/add/problem`, {
            method: "POST",
            body: JSON.stringify({
                pset_id: ID,
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
    <h1>Edit Problem Set</h1>

    <form onsubmit={editPset}>
        <label for="name">Name</label>
        <input name="name" type="text" bind:value={name}>
        <br>
        <label for="hide">Make Problem Set Hidden</label>
        <input name="hide" type="checkbox" bind:checked={hide}>
        <br>
        <input type="submit" value="Update Problem Set">
    </form>

    <h2>Problems</h2>
    <table>
    <thead>
        <tr>
            <th>Name</th>
        </tr>
    </thead>
    <tbody>
    {#each problems as problem}
        <tr class="pb-row">
            <td><a href="/admin/problem?id={problem["id"]}">{problem["name"]}</a></td>
        </tr>
    {/each}
    </tbody>
    </table>

    <h2>Add Problem</h2>
    <form onsubmit={addProblem}>
        <label for="problem-name">Problem Name</label>
        <input name="problem-name" type="text" bind:value={problemName}>
        <input type="submit" value="Add Problem">
    </form>
</div>