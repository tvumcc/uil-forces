<script lang="ts">
    import { goBack } from "$lib/navigationHistory.svelte";
    import SubmissionTable from "$lib/submissionTable.svelte";
    import { addErrorToast } from "$lib/toastStore.svelte";
    import type {Submission} from "$lib/utils"

    let params = new URLSearchParams(document.location.search)
    let page = $state(params.get("page") ?? "1")

    let submissions: Submission[] = $state([])

    async function getData() {
        const response: Response = await fetch(`/api/admin/submissions/${page}`)

        if (!response.json) {
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
        {#if page != "1"}
            <a href={`/admin/submissions?page=${Number(page) - 1}`}>Previous Page</a>
        {/if}
        <p>Page {page}</p>
        {#if submissions.length === 20}
            <a href={`/admin/submissions?page=${Number(page) + 1}`}>Next Page</a>
        {/if}
        <SubmissionTable {submissions} showUsers={true} showDelete={true}/>
    {/await}
</div>