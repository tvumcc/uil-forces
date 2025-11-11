<script lang="ts">
    import MenuBar from "../components/menuBar.svelte"
    import { toTzIsoString, getTzOffset, type Contest } from "../../utils"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")
    let validRequest = $state(true)
    let message = $state("")

    let contest: Contest | undefined = $state()

    let psetName = $state("")
    let problemPsetName = $state("")
    let problemName = $state("")

    async function getData() {
        let response: Response = await fetch(`/api/admin/contest/${ID}`)
        let json = await response.json()
        
        if (!response.ok) {
            validRequest = false
            message = json.description
        }

        contest = json.contest
        if (contest !== undefined) {
            contest.startTime = toTzIsoString(new Date(contest.startTime))
            contest.endTime = toTzIsoString(new Date(contest.endTime))

            console.log(contest.problems)
        }
    }

    async function editContest(event: Event) {
        event.preventDefault()

        let response: Response = await fetch("/api/admin/update/contest", {
            method: "POST",
            body: JSON.stringify({
                id: contest!.id,
                name: contest!.name,
                startTime: new Date(contest?.startTime + getTzOffset()).toISOString(),
                endTime: new Date(contest?.endTime + getTzOffset()).toISOString(),
                showPdf: contest!.showPdf,
                showLeaderboard: contest?.showLeaderboard,
                allowedLanguages: contest?.allowedLanguages 
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
                psetName: psetName,
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
                psetName: problemPsetName,
                problemName: problemName 
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok) {
            await getData()
        }
    }

    async function unlinkProblem(problemID: number) {
        let response: Response = await fetch("/api/admin/contest/unlinkproblem", {
            method: "POST",
            body: JSON.stringify({
                contestID: ID,
                problemID: problemID
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok)  {
            await getData()
        }
    }

    async function updateProblemScores() {
        let response: Response = await fetch("/api/admin/contest/updateproblems", {
            method: "POST",
            body: JSON.stringify({
                contestID: ID,
                problems: contest!.problems
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok)  {
            await getData()
        }
    }
</script>

<!-- svelte-ignore css_unused_selector -->
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
    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if validRequest && contest !== undefined}
            <form onsubmit={editContest}>
                <label for="name">Name</label>
                <input name="name" type="text" bind:value={contest.name}>
                <label for="start-time">Start Time</label>
                <input name="start-time" type="datetime-local" bind:value={contest.startTime}>
                <label for="end-time">End Time</label>
                <input name="end-time" type="datetime-local" bind:value={contest.endTime}>
                <br>
                <label for="show-pdf">Show PDF Problem Statement Viewer</label>
                <input name="show-pdf" type="checkbox" bind:checked={contest.showPdf}>
                <br>
                <label for="show-leaderboard">Show Leaderboard</label>
                <input name="show-leaderboard" type="checkbox" bind:checked={contest.showLeaderboard}>
                <br>
                <label for="allowed-languages">Allowed Languages (space separated)</label>
                <input name="allowed-languages" type="text" bind:value={contest.allowedLanguages}>
                <br>
                <input type="submit" value="Update Contest">
            </form>

            <h2>Problems</h2>
            <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Score</th>
                    <th>Penalty</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
            {#each contest!.problems as problem: ContestProblem, i}
                <tr class="pb-row">
                    <td>{problem.problem.name}</td>
                    <td><input type="text" bind:value={problem.correctScore}></td>
                    <td><input type="text" bind:value={problem.incorrectPenalty}></td>
                    <td><button onclick={async ()=>{await unlinkProblem(problem.problem.id)}}>Remove</button></td>
                </tr>
            {/each}
            </tbody>
            </table>
            <button onclick={updateProblemScores}>Update Problems and Recalculate Scores</button>

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
        {:else}
            <p>{message}</p>
        {/if}
    {/await}
</div>