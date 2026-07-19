<script lang="ts">
    import { page } from "$app/state"
    import { goBack } from "$lib/navigationHistory.svelte";
    import SubmissionTable from "$lib/submissionTable.svelte";
    import { addErrorToast } from "$lib/toastStore.svelte";
    import type {Submission} from "$lib/utils"

    let pageNum: number = $derived(Number(page.url.searchParams.get("page") ?? "1"))

    let submissions: Submission[] = $state([])

    async function getData() {
        const response: Response = await fetch(`/api/admin/submissions/${pageNum}`)

        if (!response.ok) {
            await addErrorToast(response, "Failed to load submissions list")
            goBack()
            return
        }

        const data = await response.json()
        submissions = data.submissions
    }
</script>

<div class="main-container">
    <h1>All Submissions</h1>

    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if pageNum > 1}
            <a href={`/admin/submissions?page=${pageNum - 1}`}>Previous Page</a>
        {/if}
        <p>Page {pageNum}</p>
        {#if submissions.length === 20}
            <a href={`/admin/submissions?page=${pageNum + 1}`}>Next Page</a>
        {/if}
        <SubmissionTable {submissions} showUsers={true} showActions={true}/>
    {/await}
</div>