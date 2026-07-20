<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/state";
    import { goto } from "$app/navigation";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";
    import { toTzIsoString, getTzOffset, type Contest, type ContestProblem, csrfFetch } from "$lib/utils"

    let ID = page.url.searchParams.get("id")
    let contest: Contest | undefined = $state()
    let loading = $state(true)

    let psetName = $state("")
    let problemPsetName = $state("")
    let problemName = $state("")
    let confirmingUnlinkID: number | null = $state(null)

    async function getData() {
        const response: Response = await fetch(`/api/admin/contest/${ID}`)

        if (!response.ok) {
            await addErrorToast(response, "Failed to load contest")
            goto("/admin/contests")
            return
        }

        const data = await response.json()
        contest = data.contest
        if (contest !== undefined) {
            contest.startTime = toTzIsoString(new Date(contest.startTime))
            contest.endTime = toTzIsoString(new Date(contest.endTime))
        }
        loading = false
    }

    async function editContest(event: Event) {
        event.preventDefault()

        let newStartTime
        let newEndTime
        try {
            newStartTime = new Date(contest!.startTime + getTzOffset()).toISOString()
            newEndTime = new Date(contest!.endTime + getTzOffset()).toISOString()
        } catch {
            addToast("Failed to update contest: invalid date(s)", ToastType.Error)
            return
        }

        const response: Response = await csrfFetch("/api/admin/contest/update", "POST", {
            id: contest!.id,
            name: contest!.name,
            startTime: newStartTime,
            endTime: newEndTime,
            showPdf: contest!.showPdf,
            showLeaderboard: contest!.showLeaderboard,
            allowedLanguages: contest!.allowedLanguages
        })

        if (response.ok) {
            await getData()
            addToast("Updated contest", ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to update contest")
        }
    }

    async function addProblemSet(event: Event) {
        event.preventDefault()

        const response: Response = await csrfFetch(`/api/admin/contest/${ID}/add/pset`, "POST", {
            psetName: psetName,
        })

        if (response.ok) {
            await getData()
            addToast("Added problem set to contest", ToastType.Success)
            psetName = ""
        } else {
            await addErrorToast(response, "Failed to add problem set to contest")
        }
    }

    async function addProblem(event: Event) {
        event.preventDefault()

        const response: Response = await csrfFetch(`/api/admin/contest/${ID}/add/problem`, "POST", {
            psetName: problemPsetName,
            problemName: problemName
        })

        if (response.ok) {
            await getData()
            addToast("Added problem to contest", ToastType.Success)
            problemPsetName = ""
            problemName = ""
        } else {
            await addErrorToast(response, "Failed to add problem to contest")
        }
    }

    async function unlinkProblem(problemID: number) {
        const response: Response = await csrfFetch("/api/admin/contest/unlinkproblem", "POST", {
            contestID: ID,
            problemID: problemID
        })

        confirmingUnlinkID = null

        if (response.ok) {
            await getData()
            addToast("Removed problem from contest", ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to remove problem from contest")
        }
    }

    async function updateProblemScores() {
        const response: Response = await csrfFetch("/api/admin/contest/updateproblems", "POST", {
            contestID: ID,
            problems: contest!.problems
        })

        if (response.ok) {
            await getData()
            addToast("Updated problem scoring and refreshed user scores", ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to update problem scoring")
        }
    }

    onMount(() => {
        getData()
    })
</script>

<div class="main-container">
    {#if loading}
        <div class="panel skeleton"></div>
    {:else if contest !== undefined}
        <header class="hero">
            <h1>{contest.name}</h1>
        </header>

        <section class="panel">
            <h2 class="section-header">Edit Details</h2>
            <form class="stacked-form" onsubmit={editContest}>
                <div class="field">
                    <label for="name">Name</label>
                    <input name="name" type="text" bind:value={contest.name}>
                </div>

                <div class="field">
                    <label for="start-time">Start Time</label>
                    <div class="input-with-button">
                        <input name="start-time" type="datetime-local" bind:value={contest.startTime}>
                        <button type="button" class="btn" onclick={() => {contest!.startTime = toTzIsoString(new Date())}}>now</button>
                    </div>
                </div>

                <div class="field">
                    <label for="end-time">End Time</label>
                    <div class="input-with-button">
                        <input name="end-time" type="datetime-local" bind:value={contest.endTime}>
                        <button type="button" class="btn" onclick={() => {contest!.endTime = toTzIsoString(new Date())}}>now</button>
                    </div>
                </div>

                <div class="field">
                    <label for="allowed-languages">Allowed Languages (space separated; "Java" and "Python" only)</label>
                    <input name="allowed-languages" type="text" bind:value={contest.allowedLanguages}>
                </div>

                <div class="checkbox-row">
                    <label class="checkbox-field">
                        <input name="show-pdf" type="checkbox" bind:checked={contest.showPdf}>
                        Show problem statement PDF viewer
                    </label>
                    <label class="checkbox-field">
                        <input name="show-leaderboard" type="checkbox" bind:checked={contest.showLeaderboard}>
                        Show leaderboard
                    </label>
                </div>

                <button type="submit" class="btn btn-primary">Update Contest</button>
            </form>
        </section>

        <div class="panel-grid spaced">
            <section class="panel spaced">
                <h2 class="section-header">Add Problem</h2>
                <form class="stacked-form" onsubmit={addProblem}>
                    <div class="field">
                        <label for="problem-pset-name">Problem Set Name</label>
                        <input name="problem-pset-name" type="text" bind:value={problemPsetName}>
                    </div>
                    <div class="field">
                        <label for="problem-name">Problem Name</label>
                        <input name="problem-name" type="text" bind:value={problemName}>
                    </div>
                    <button type="submit" class="btn btn-primary">Add Problem</button>
                </form>
            </section>

            <section class="panel spaced">
                <h2 class="section-header">Add Problem Set</h2>
                <form class="stacked-form" onsubmit={addProblemSet}>
                    <div class="field">
                        <label for="pset-name">Problem Set Name</label>
                        <input name="pset-name" type="text" bind:value={psetName}>
                    </div>
                    <button type="submit" class="btn btn-primary">Add Problem Set</button>
                </form>
            </section>
        </div>

        <section class="panel spaced">
            <h2 class="section-header">Edit Problems</h2>
            {#if contest.problems && contest.problems.length > 0}
                <table class="problem-table">
                    <thead>
                        <tr>
                            <th>name</th>
                            <th>score</th>
                            <th>penalty</th>
                            <th>grading timeout (seconds)</th>
                            <th>action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each contest.problems as problem}
                            <tr>
                                <td><a href="/admin/problem?id={problem.problem.id}" target="_blank">{problem.problem.name}</a></td>
                                <td><input class="cell-input" type="text" bind:value={problem.correctScore}></td>
                                <td><input class="cell-input" type="text" bind:value={problem.incorrectPenalty}></td>
                                <td><input class="cell-input" type="text" bind:value={problem.gradingTimeout}></td>
                                <td>
                                    {#if confirmingUnlinkID === problem.problem.id}
                                        <span class="confirm-text">Remove?</span>
                                        <button class="btn btn-danger" onclick={() => unlinkProblem(problem.problem.id)}>Yes</button>
                                        <button class="btn" onclick={() => confirmingUnlinkID = null}>No</button>
                                    {:else}
                                        <button class="btn btn-danger-outline" onclick={() => confirmingUnlinkID = problem.problem.id}>Remove</button>
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
                <button class="btn btn-primary spaced-btn" onclick={updateProblemScores}>Update and recalculate scores</button>
            {:else}
                <p class="empty-state">No problems added to this contest yet.</p>
            {/if}
        </section>

    {/if}
</div>

<style>
    .problem-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }
    .problem-table th {
        color: #64748b;
        font-weight: normal;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
        text-align: left;
        padding: 8px 10px;
        border-bottom: 1px solid #1e293b;
    }
    .problem-table td {
        padding: 8px 10px;
        border-bottom: 1px solid #131d2e;
    }
    .cell-input {
        width: 70px;
        background-color: #0f1a2e;
        color: white;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 6px 8px;
        font-family: inherit;
        font-size: 13px;
    }
    .cell-input:focus {
        outline: none;
        border-color: #00d492;
    }
</style>