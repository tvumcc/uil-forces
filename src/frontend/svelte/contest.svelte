<script lang="ts">
    import { onMount } from "svelte"
    import Status from "./components/status.svelte"
    import MenuBar from "./components/menubar.svelte"
    import { get } from "svelte/store";

    let params = new URLSearchParams(document.location.search)
    let id = params.get("id")

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
        let json = await response.json()
        submissions = json["submissions"]

        let count = json["estimated_wait"]
        let interval_id = setInterval(async () => {
            if (count > 0) {
                let response: Response = await fetch("/api/contest/" + id)
                let json = await response.json()
                submissions = json["submissions"]
                count--;
            } else {
                clearInterval(interval_id)
            }
        }, 1000)
    }

    async function poll_submissions() {
        for (let i = 0; i < 5; i++) {
        }
    }

    $effect(() => {
        (async () => {
            if (files) {
                for (let file of files) {
                    file_text = await file.text()
                    file_name = file.name
                }
            }
        })()
    })

    onMount(() => {
        getData()
    })
</script>

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

    .horizontal-split {
        display: grid;
        grid-template-columns: 1fr 1fr;
        width: 100%;
        height: 100%;
    }

    .submit-panel {
        margin: 0;
        display: flex;
        align-items: center;
        flex-direction: column;
    }    
    
    #pdf-viewer {
        background-color: black;
        height: 100vh;
    }
</style>

<div class="horizontal-split">
    <div id="pdf-viewer">
        {#if selected_problem_id != -1}
            <embed type="application/pdf" src={`/api/problem/${selected_problem_id}/pdf#toolbar=0&navpanes=0`} width="100%" height="100%">
        {:else}
            <p>No Problem Selected</p>
        {/if}
    </div>
    <div class="submit-panel">
        <MenuBar />
        <div class="main-container">
            <h1>{contest_name}</h1>
            <h2>Submit Code</h2>
            <form onsubmit={submit_problem}>
                <div>
                    <select bind:value={selected_problem_id}>
                        {#each problems as problem}
                            <option value="{problem["id"]}">{problem["name"]}</option>
                        {/each}
                    </select>
                </div>
                <div>
                    <input type="file" bind:files>
                </div>
                <div>
                    <input type="submit" value="Submit">
                </div>
            </form>

            <br>
            {#if files}
                <pre style="tab-size:4;">{file_text}</pre>
            {/if}

            <h2>Submissions</h2>
            {#if submissions.length > 0}
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Problem</th>
                            <th>Status</th>
                            <th>Code</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each submissions as submission}
                            <tr>
                                <td>{submission["submit_time"]}</td>
                                <td>{submission["problem"]["name"]}</td>
                                <td style="width: 175px;"><Status status_code={submission["status"]} fit_text={false}/></td>
                                <td style="width: 100px;"><a href="/submission?id={submission["id"]}">View Code</a></td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            {:else}
                <p>No submissions at this time</p>
            {/if}
        </div>

    </div>
</div>