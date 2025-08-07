<script lang="ts">
    import { onMount } from "svelte"

    let params = new URLSearchParams(document.location.search)

    let id = params.get("id")

    let contest_name = ""

    async function getData() {
        let response: Response = await fetch("/api/contest/" + id)
        let json = await response.json()
        contest_name = json["name"]
    }

    onMount(getData)
</script>

<h1>{contest_name}</h1>