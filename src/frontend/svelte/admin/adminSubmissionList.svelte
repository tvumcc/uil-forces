<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "../components/menuBar.svelte"
    import SubmissionTable from "../components/submissionTable.svelte";

    let params = new URLSearchParams(document.location.search)
    let page = params.get("page")
    if (page === null) {
        page = "1"
    }

    let submissions = $state([])

    async function getData() {
        let response: Response = await fetch(`/api/admin/submissions/${page}`)
        let json = await response.json()
        submissions = json["submissions"]
    }

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
    <h1>All Submissions</h1>

    {#if page != "1"}
        <a href={`/admin/submissions?page=${Number(page) - 1}`}>Previous Page</a>
    {/if}
    <p>Page {page}</p>
    {#if submissions.length === 20}
        <a href={`/admin/submissions?page=${Number(page) + 1}`}>Next Page</a>
    {/if}
    <SubmissionTable {submissions} showUsers={true} showDelete={true}/>
</div>
