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
            <section class="panel">
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

            <section class="panel">
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
                            <th class="actions-col">action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each contest.problems as problem}
                            <tr>
                                <td><a href="/admin/problem?id={problem.problem.id}" target="_blank">{problem.problem.name}</a></td>
                                <td><input class="cell-input" type="text" bind:value={problem.correctScore}></td>
                                <td><input class="cell-input" type="text" bind:value={problem.incorrectPenalty}></td>
                                <td><input class="cell-input" type="text" bind:value={problem.gradingTimeout}></td>
                                <td class="actions-cell">
                                    {#if confirmingUnlinkID === problem.problem.id}
                                        <span class="confirm-text">Remove?</span>
                                        <button class="btn btn-danger" onclick={() => unlinkProblem(problem.problem.id)}>yes</button>
                                        <button class="btn" onclick={() => confirmingUnlinkID = null}>no</button>
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
    .panel.spaced {
        margin-top: 16px;
    }
    .skeleton {
        min-height: 200px;
        background: linear-gradient(90deg, #0b1220 0%, #131d2e 50%, #0b1220 100%);
        background-size: 200% 100%;
        animation: shimmer 1.4s ease-in-out infinite;
    }
    @media (prefers-reduced-motion: reduce) {
        .skeleton { animation: none; }
    }
    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }

    .section-header {
        font-size: 15px;
        letter-spacing: 1px;
        margin: 0 0 14px 0;
        color: #e2e8f0;
    }

    .panel-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
    }
    .panel-grid.spaced {
        margin-top: 16px;
    }
    @media (max-width: 700px) {
        .panel-grid { grid-template-columns: 1fr; }
    }

    .stacked-form {
        display: flex;
        flex-direction: column;
        gap: 14px;
        max-width: 480px;
    }

    .field {
        display: flex;
        flex-direction: column;
        gap: 5px;
    }

    label {
        font-size: 12px;
        letter-spacing: 0.5px;
        color: #64748b;
    }

    input[type="text"],
    input[type="datetime-local"] {
        background-color: #0f1a2e;
        color: white;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 8px 10px;
        font-family: inherit;
        font-size: 14px;
        width: 100%;
        box-sizing: border-box;
    }
    input[type="text"]:focus,
    input[type="datetime-local"]:focus {
        outline: none;
        border-color: #00d492;
    }

    .input-with-button {
        display: flex;
        gap: 8px;
    }
    .input-with-button input {
        flex: 1;
    }

    .checkbox-row {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .checkbox-field {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: #cbd5e1;
        text-transform: none;
        letter-spacing: normal;
        cursor: pointer;
    }
    .checkbox-field input {
        accent-color: #00d492;
        width: 15px;
        height: 15px;
    }

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

    .actions-col { text-align: right; }
    .actions-cell {
        text-align: right;
        white-space: nowrap;
    }

    .empty-state {
        color: #64748b;
        font-size: 14px;
        margin: 0;
        padding: 6px 0;
    }

    .spaced-btn {
        margin-top: 14px;
    }

    .btn {
        background-color: #0f1a2e;
        color: #cbd5e1;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 7px 14px;
        font-family: inherit;
        font-size: 13px;
        cursor: pointer;
        margin-left: 6px;
        transition: border-color 0.15s ease, color 0.15s ease;
    }
    .btn:first-child {
        margin-left: 0;
    }
    .btn:hover {
        border-color: #00d492;
        color: white;
    }
    @media (prefers-reduced-motion: reduce) {
        .btn { transition: none; }
    }

    .btn-primary {
        background-color: #00d492;
        color: #030712;
        border: none;
        font-weight: bold;
        margin-left: 0;
    }
    .btn-primary:hover {
        opacity: 0.85;
        color: #030712;
    }

    .btn-danger-outline {
        color: #f87171;
    }
    .btn-danger-outline:hover {
        border-color: #f87171;
        color: #f87171;
    }

    .btn-danger {
        background-color: #f87171;
        border-color: #f87171;
        color: #030712;
        font-weight: bold;
    }
    .btn-danger:hover {
        opacity: 0.85;
        color: #030712;
    }

    .confirm-text {
        font-size: 12px;
        color: #f87171;
        margin-right: 4px;
    }
</style>