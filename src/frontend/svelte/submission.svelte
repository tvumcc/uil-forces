<script lang="ts">
    import Status from "./components/status.svelte"
    import MenuBar from "./components/menubar.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    async function get_data() {
        let response: Response = await fetch(`/api/submission/${ID}`)
        let json = await response.json()
        return json
    }

    let submissionPromise = get_data()
</script>

<style>
    @import "../style.css";
</style>

<MenuBar />
<div class="main-container">
    {#await submissionPromise then submission}
        <h1>Submission</h1>

        <p>User: {submission.user.username}</p>
        <p>Submit Time: {submission.submit_time}</p>
        <p>Status: <Status statusCode={submission.status} fitText={true}/></p>
        {#if submission.contest_profile}
            <p>Contest: <a href="/contest?id={submission.contest_profile.contest.id}">{submission.contest_profile.contest.name}</a></p>
        {/if}

        <h2>Submitted Code</h2>
        <pre>{submission.code}</pre>

        <h2>Output</h2>
        <pre>{submission.output}</pre>
    {/await}
</div>