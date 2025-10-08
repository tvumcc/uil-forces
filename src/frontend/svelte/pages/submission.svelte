<script lang="ts">
    import Status from "../components/status.svelte"
    import MenuBar from "../components/menuBar.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    async function getData() {
        let response: Response = await fetch(`/api/submission/${ID}`)
        let json = await response.json()
        return json
    }
</script>

<style>
    @import "../../style.css";
</style>

<MenuBar />
<div class="main-container">
    {#await getData()}
        <p>Loading...</p>
    {:then submission}
        <h1>Submission</h1>

        <p>User: {submission.user.username}</p>
        <p>Submit Time: {new Date(submission.submit_time).toLocaleString()}</p>
        <p>Status: <Status statusCode={submission.status} fitText={true}/></p>
        {#if submission.contest_profile}
            <p>Contest: <a href="/contest?id={submission.contest_profile.contest.id}">{submission.contest_profile.contest.name}</a></p>
        {/if}

        {#if submission.code !== undefined}
            <h2>Submitted Code</h2>
            <pre>{submission.code}</pre>
        {/if}

        {#if submission.output !== undefined}
            <h2>Output</h2>
            <pre>{submission.output}</pre>
        {/if}
    {/await}
</div>