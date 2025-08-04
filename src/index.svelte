<script lang="ts">
    import Home from "./home.svelte"
    import Login from "./login.svelte"
    
    let current_page = $state("home")
</script>

{#if current_page == "home"}
    <Home bind:current_page={current_page}/>
{:else if current_page == "login"}
    <Login bind:current_page={current_page}/>
{/if}