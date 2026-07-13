<script lang="ts">
    import { goto } from "$app/navigation";

    import { addToast, ToastType } from "$lib/toastStore.svelte";

    import { toTzIsoString, getTzOffset, type Contest, csrfFetch } from "$lib/utils"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let contest: Contest | undefined = $state()

    let psetName = $state("")
    let problemPsetName = $state("")
    let problemName = $state("")

    async function getData() {
        const response: Response = await fetch(`/api/admin/contest/${ID}`)
        const data = await response.json()
        
        if (!response.ok) {
            let error_message
            if (data.error === "not_found") {
                error_message = "Contest does not exist"
            } else {
                error_message = "Failed to load contest page"
            }

            addToast(error_message, ToastType.Error)
            goto("/admin/contests")
            return
        }

        contest = data.contest
        if (contest !== undefined) {
            contest.startTime = toTzIsoString(new Date(contest.startTime))
            contest.endTime = toTzIsoString(new Date(contest.endTime))
        }
    }

    async function editContest(event: Event) {
        event.preventDefault()

        const response: Response = await csrfFetch("/api/admin/update/contest", "POST", JSON.stringify({
            id: contest!.id,
            name: contest!.name,
            startTime: new Date(contest?.startTime + getTzOffset()).toISOString(),
            endTime: new Date(contest?.endTime + getTzOffset()).toISOString(),
            showPdf: contest!.showPdf,
            showLeaderboard: contest?.showLeaderboard,
            allowedLanguages: contest?.allowedLanguages 
        }))

        if (response.ok) {
            await getData()
        }
    }

    async function addProblemSet(event: Event) {
        event.preventDefault()

        let response: Response = await csrfFetch(`/api/admin/contest/${ID}/add/pset`, "POST", JSON.stringify({
            psetName: psetName,
        }))

        if (response.ok) {
            await getData()
        }
    }

    async function addProblem(event: Event) {
        event.preventDefault()

        let response: Response = await csrfFetch(`/api/admin/contest/${ID}/add/problem`, "POST", JSON.stringify({
            psetName: problemPsetName,
            problemName: problemName 
        }))

        if (response.ok) {
            await getData()
        }
    }

    async function unlinkProblem(problemID: number) {
        let response: Response = await csrfFetch("/api/admin/contest/unlinkproblem", "POST", JSON.stringify({
            contestID: ID,
            problemID: problemID
        }))

        if (response.ok)  {
            await getData()
        }
    }

    async function updateProblemScores() {
        let response: Response = await csrfFetch("/api/admin/contest/updateproblems", "POST", JSON.stringify({
            contestID: ID,
            problems: contest!.problems
        }))

        if (response.ok)  {
            await getData()
        }
    }
</script>

<div class="main-container">
    <h1>Edit Contest</h1>
    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if contest !== undefined}
            <form onsubmit={editContest}>
                <table>
                    <tbody>
                        <tr>
                            <td><label for="name">Name</label></td>
                            <td><input name="name" type="text" bind:value={contest.name} class="full-width"></td>
                        </tr>
                        <tr>
                            <td><label for="start-time">Start Time</label></td>
                            <td><input name="start-time" type="datetime-local" bind:value={contest.startTime} class="full-width"></td>
                        </tr>
                        <tr>
                            <td><label for="end-time">End Time</label></td>
                            <td><input name="end-time" type="datetime-local" bind:value={contest.endTime} class="full-width"></td>
                        </tr>
                        <tr>
                            <td><label for="allowed-languages">Allowed Languages (space separated)</label></td>
                            <td><input name="allowed-languages" type="text" bind:value={contest.allowedLanguages} class="full-width"></td>
                        </tr>
                        <tr>
                            <td><label for="show-pdf">Show PDF Problem Statement Viewer</label></td>
                            <td><input name="show-pdf" type="checkbox" bind:checked={contest.showPdf}></td>
                        </tr>
                        <tr>
                            <td><label for="show-leaderboard">Show Leaderboard</label></td>
                            <td><input name="show-leaderboard" type="checkbox" bind:checked={contest.showLeaderboard}></td>
                        </tr>
                    </tbody>
                </table>
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
                <table>
                    <tbody>
                        <tr>
                            <td><label for="problem-pset-name">Problem Set Name</label></td>
                            <td><input name="problem-pset-name" type="text" bind:value={problemPsetName}></td>
                        </tr>
                        <tr>
                            <td><label for="problem-name">Problem Name</label></td>
                            <td><input name="problem-name" type="text" bind:value={problemName}></td>
                        </tr>
                    </tbody>
                </table>
                <input type="submit" value="Add Problem">
            </form>
        {/if}
    {/await}
</div>

<style>
    table {
        border-collapse: collapse;
    }

    td {
        padding: 4px;
    }

    .pb-row td {
        border: 0;
        margin: 0;
        padding: 8px;
        text-align: left;
    }
    
    .full-width {
        width: 100%;
    }
</style>