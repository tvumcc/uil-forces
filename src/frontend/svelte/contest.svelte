<script lang="ts">
    import { onMount } from "svelte"

    let params = new URLSearchParams(document.location.search)

    let id = params.get("id")

    let contest_name = $state("")
    let problems = $state([])

    let selected_problem_id = $state()
    let files: FileList = $state()!
    let file_text = $state()

    async function getData() {
        let response: Response = await fetch("/api/contest/" + id)
        let json = await response.json()
        console.log(json)
        contest_name = json["name"]
        problems = json["problem_set"]["problems"]
    }

    async function submit_problem(event: Event) {
        event.preventDefault()
        let response: Response = await fetch("/api/contest/submit", {
            method: "POST",
            body: JSON.stringify({
                contest_id: id,
                problem_id: selected_problem_id,
                code: file_text
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })
        console.log("sup lol")
    }

    $effect(() => {
        (async () => {
            if (files) {
                for (let file of files) {
                    file_text = await file.text()
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

