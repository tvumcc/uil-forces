<script lang="ts">
    import { onMount } from "svelte"

    let { current_page = $bindable() } = $props()
    let switch_to_login = () => current_page = "login"

    let data: string = $state("")
    async function getData() {
        let response: Response = await fetch("/api/top")
        let uhh = await response.json()
        data = uhh["data"]
    }

    onMount(getData)
</script>

<h1>Home Page</h1>

<p>Some data: {data}</p>
<button onclick={switch_to_login}>
    Login
</button>