<script lang="ts">
    import Status from "$lib/status.svelte"
    import {csrfFetch, type Submission} from "$lib/utils"
    import { addErrorToast, addToast, ToastType } from "./toastStore.svelte";

    let {
        submissions, 
        showUsers,
        showActions = false
    } = $props()

    async function deleteSubmission(id: number) {
        const response: Response = await csrfFetch(`/api/admin/submission/${id}/delete`, "DELETE")

        if (!response.ok) {
            await addErrorToast(response, "Failed to delete submission")
            return
        }

        submissions = submissions.filter((submission: Submission) => submission.id !== id)
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
    <table>
        <thead>
            <tr>
                <th>Time</th>
                {#if showUsers}
                    <th>User</th>
                {/if}
                <th>Problem</th>
                <th>Language</th>
                <th>Status</th>
                <th>Code</th>
                {#if showActions}
                    <th>Delete</th>
                    <th>Regrade</th>
                {/if}
            </tr>
        </thead>
        <tbody>
            {#each submissions as submission}
                <tr>
                    <td>{new Date(submission.submitTime).toLocaleString()}</td>
                    {#if showUsers}
                        <td>{submission.user.username}</td>
                    {/if}
                    <td>{submission.problem.name}</td>
                    <td>{submission.language}</td>
                    <td style="width: 175px;"><Status statusCode={submission.status} fitText={false}/></td>
                    <td style="width: 80px;"><a href="/submission?id={submission.id}">View Code</a></td>
                    {#if showActions}
                        <td style="width: 80px;"><button onclick={() => deleteSubmission(submission.id)}>Delete</button></td>
                        <td style="width: 80px;"><button onclick={() => regradeSubmission(submission.id)}>Regrade</button></td>
                    {/if}
                </tr>
            {/each}
        </tbody>
    </table>
{:else}
    <p>No submissions at this time</p>
{/if}

<style>
    @import "../style.css";

    table {
        width: 100%;
        margin: 0;
        border-collapse: collapse;
    }

    td {
        border: 1px gray solid;
        margin: 0;
        padding: 8px;
        text-align: center;
    }
</style>