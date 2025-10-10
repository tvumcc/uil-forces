<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "../components/menuBar.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let practiceSite = $state(false)
    let dockerGrading = $state(false)

    async function getData() {
        let response: Response = await fetch(`/api/admin/settings`)
        let json = await response.json()
        practiceSite = json["settings"]["practice_site"]
        dockerGrading = json["settings"]["docker_grading"]
    }

    async function editSettings(event: Event) {
        event.preventDefault()

        let response: Response = await fetch("/api/admin/update/settings", {
            method: "POST",
            body: JSON.stringify({
                practice_site: practiceSite,
                docker_grading: dockerGrading
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok) {
            await getData()
        }
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
    <h1>Site-wide Settings</h1>

    <form onsubmit={editSettings}>
        <label for="practice-site">Enable Practice</label>
        <input name="practice-site" type="checkbox" bind:checked={practiceSite}>
        <br>
        <label for="docker-grading">Use Docker Grading</label>
        <input name="docker-grading" type="checkbox" bind:checked={dockerGrading}>
        <br>
        <input type="submit" value="Update Settings">
    </form>
</div>
