<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "../components/menuBar.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let name = $state("")
    let hide = $state(true)
    let problems = $state([])

    async function getData() {
        let response: Response = await fetch(`/api/admin/pset/${ID}`)
        let json = await response.json()
        name = json["pset"]["name"]
        hide = json["pset"]["hide"]
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

    // async function addProblem(event: Event) {
    //     event.preventDefault()

    //     let response: Response = await fetch(`/api/admin/pset/${ID}/add/problem`, {
    //         method: "POST",
    //         body: JSON.stringify({
    //             problem_name: problemName 
    //         }),
    //         headers: {
    //             "Content-Type": "application/json; charset=UTF-8"
    //         }
    //     })

    //     if (response.ok) {
    //         await getData()
    //     }
    // }

    // async function unlinkProblem(problem_id: number) {
    //     let response: Response = await fetch("/api/admin/contest/unlinkproblem", {
    //         method: "POST",
    //         body: JSON.stringify({
    //             contest_id: ID,
    //             problem_id: problem_id
    //         }),
    //         headers: {
    //             "Content-Type": "application/json; charset=UTF-8"
    //         }
    //     })

    //     if (response.ok)  {
    //         await getData()
    //     }
    // }

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
</div>