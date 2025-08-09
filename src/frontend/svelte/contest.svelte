<script lang="ts">
    import { onMount } from "svelte"

    let params = new URLSearchParams(document.location.search)
    let id = params.get("id")

    let status_str = ["Pending", "Accepted", "Wrong Answer", "Compile Error", "Runtime Error", "Time Limit Exceeded"]

    let contest_name = $state("")
    let problems = $state([])
    let submissions = $state([])

    let selected_problem_id = $state(-1)
    let files: FileList = $state()!
    let file_text = $state()
    let file_name = $state()

    async function getData() {
        let response: Response = await fetch("/api/contest/" + id)
        let json = await response.json()
        console.log(json)
        contest_name = json["name"]
        problems = json["problem_set"]["problems"]
        submissions = json["submissions"]
    }

    async function submit_problem(event: Event) {
        event.preventDefault()
        let response: Response = await fetch("/api/contest/submit", {
            method: "POST",
            body: JSON.stringify({
                contest_id: id,
                problem_id: selected_problem_id,
                code: file_text,
                filename: file_name
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })
    }

    $effect(() => {
        (async () => {
            if (files) {
                for (let file of files) {
                    file_text = await file.text()
                    file_name = file.name
                    console.log(file_text)
                }
            }
        })()
    })

    onMount(getData)
</script>

<h1>{contest_name}</h1>
<form onsubmit={submit_problem}>
    <select bind:value={selected_problem_id}>
        {#each problems as problem}
            <option value="{problem["id"]}">{problem["name"]}</option>
        {/each}
    </select>
    <input type="file" bind:files>
    <input type="submit" value="Submit">
</form>

<br>
{#if files}
    <pre style="tab-size:4;">{file_text}</pre>
{/if}

<h2>Submissions</h2>
<table>
    <thead>
        <tr>
            <th>Time</th>
            <th>User</th>
            <th>Problem</th>
            <th>Status</th>
            <th>Code</th>
        </tr>
    </thead>
    <tbody>
        {#each submissions as submission}
            <tr>
                <th>{submission["submit_time"]}</th>
                <th>{submission["user"]["username"]}</th>
                <th>{submission["problem"]["name"]}</th>
                <th>{status_str[submission["status"]]}</th>
                <th><a href="/submission?id={submission["id"]}">View Code</a></th>
            </tr>
        {/each}
    </tbody>
</table>
