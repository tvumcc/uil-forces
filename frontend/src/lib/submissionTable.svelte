<script lang="ts">
    import Status from "$lib/status.svelte"
    import {csrfFetch, type Submission} from "$lib/utils"
    import { addErrorToast, addToast, ToastType } from "./toastStore.svelte";

    let {
        submissions, 
        showUsers,
        showActions = false
    } = $props()

    let confirmingDeleteID: number | null = $state(null)

    async function deleteSubmission(id: number) {
        const response: Response = await csrfFetch(`/api/admin/submission/${id}/delete`, "DELETE")
        if (!response.ok) {
            await addErrorToast(response, "Failed to delete submission")
            confirmingDeleteID = null
            return
        }
        submissions = submissions.filter((submission: Submission) => submission.id !== id)
        confirmingDeleteID = null
    }

    async function regradeSubmission(id: number) {
        const response: Response = await csrfFetch(`/api/admin/submission/${id}/regrade`, "POST")
        if (!response.ok) {
            await addErrorToast(response, "Failed to regrade submission")
            return
        }
        addToast(`Regrade of submission ${id} is queued, refresh page to view result`, ToastType.Info)
    }
</script>

{#if submissions.length > 0}
    <table class="submission-table">
        <thead>
            <tr>
                <th>time</th>
                {#if showUsers}
                    <th>user</th>
                {/if}
                <th>problem</th>
                <th>language</th>
                <th>status</th>
                <th>code</th>
                {#if showActions}
                    <th>actions</th>
                {/if}
            </tr>
        </thead>
        <tbody>
            {#each submissions as submission}
                <tr>
                    <td class="dim">{new Date(submission.submitTime).toLocaleString()}</td>
                    {#if showUsers}
                        <td>{submission.user.username}</td>
                    {/if}
                    <td>{submission.problem.name}</td>
                    <td class="mono">{submission.language}</td>
                    <td><Status statusCode={submission.status} fitText={false}/></td>
                    <td><a href="/submission?id={submission.id}">View Code</a></td>
                    {#if showActions}
                        <td>
                            {#if confirmingDeleteID === submission.id}
                                <span class="confirm-text">Delete?</span>
                                <button class="btn btn-danger" onclick={() => deleteSubmission(submission.id)}>Yes</button>
                                <button class="btn" onclick={() => confirmingDeleteID = null}>No</button>
                            {:else}
                                <button class="btn" onclick={() => regradeSubmission(submission.id)}>Regrade</button>
                                <button class="btn btn-danger-outline" onclick={() => confirmingDeleteID = submission.id}>Delete</button>
                            {/if}
                        </td>
                    {/if}
                </tr>
            {/each}
        </tbody>
    </table>
{:else}
    <p class="empty-state">No submissions at this time.</p>
{/if}

<style>
    .submission-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }

    th {
        color: #64748b;
        font-weight: normal;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
        text-align: left;
        padding: 8px 10px;
        border-bottom: 1px solid #1e293b;
        white-space: nowrap;
    }

    td {
        padding: 9px 10px;
        border-bottom: 1px solid #131d2e;
        text-align: left;
        white-space: nowrap;
    }
</style>