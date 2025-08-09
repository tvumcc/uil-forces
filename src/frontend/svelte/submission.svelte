<script lang="ts">
    let params = new URLSearchParams(document.location.search)
    let id = params.get("id")

    let status_str = ["Pending", "Accepted", "Wrong Answer", "Compile Error", "Runtime Error", "Time Limit Exceeded"]

    async function get_data() {
        let response: Response = await fetch("/api/submission/" + id)
        let json = await response.json()
        console.log(json)
        if (json["message"]) {
            console.log("invalid")
        }

        return json
    }

    let submission_promise = get_data()
</script>

{#await submission_promise}
    <p>Fetching submission</p>
{:then submission}
    <h1>Submission</h1>

    <p>User: {submission.user.username}</p>
    <p>Submit Time: {submission.submit_time}</p>
    <p>Status: {status_str[submission.status]}</p>
    {#if submission.contest_profile}
        <p>Contest: {submission.contest_profile.contest.name}</p>
    {/if}

    <h2>Submitted Code</h2>
    <pre>{submission.code}</pre>

    <h2>Output</h2>
    <pre>{submission.output}</pre>
{/await}

