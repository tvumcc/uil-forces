<script lang="ts">
    import Status from "./components/status.svelte"
    import MenuBar from "./components/menubar.svelte"

    let params = new URLSearchParams(document.location.search)
    let id = params.get("id")

    async function get_data() {
        let response: Response = await fetch("/api/submission/" + id)
        let json = await response.json()
        if (json["message"]) {
            console.log("invalid")
        }

        return json
    }

    let submission_promise = get_data()
</script>

<style>
    @import "../style.css";
</style>

<MenuBar />
<div class="main-container">
    {#await submission_promise then submission}
        <h1>Submission</h1>

        <p>User: {submission.user.username}</p>
        <p>Submit Time: {submission.submit_time}</p>
        <p>Status: <Status status_code={submission.status} fit_text={true}/></p>
        {#if submission.contest_profile}
            <p>Contest: {submission.contest_profile.contest.name}</p>
        {/if}

        <h2>Submitted Code</h2>
        <pre>{submission.code}</pre>

        <h2>Output</h2>
        <pre>{submission.output}</pre>
    {/await}
</div>