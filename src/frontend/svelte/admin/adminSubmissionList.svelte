<script lang="ts">
    import MenuBar from "../components/menuBar.svelte"
    import SubmissionTable from "../components/submissionTable.svelte";
    import type {Submission} from "../../utils"

    let params = new URLSearchParams(document.location.search)
    let page = $state(params.get("page") ?? "1")
    let validRequest = $state(true)
    let message = $state("")

    let submissions: Submission[] = $state([])

    async function getData() {
        let response: Response = await fetch(`/api/admin/submissions/${page}`)
        let json = await response.json()

        if (!response.json) {
            validRequest = false
            message = json.description
        }

        submissions = json.submissions
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
    <h1>All Submissions</h1>

    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if validRequest}
            {#if page != "1"}
                <a href={`/admin/submissions?page=${Number(page) - 1}`}>Previous Page</a>
            {/if}
            <p>Page {page}</p>
            {#if submissions.length === 20}
                <a href={`/admin/submissions?page=${Number(page) + 1}`}>Next Page</a>
            {/if}
            <SubmissionTable {submissions} showUsers={true} showDelete={true}/>
        {:else}
            <p>{message}</p>
        {/if}
    {/await}
</div>
