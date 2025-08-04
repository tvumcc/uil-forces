<script lang="ts">
    let { current_page = $bindable() } = $props()

    let switch_to_home = () => current_page = "home"
</script>

<h1>Login Page</h1>

<button onclick={switch_to_home}>
    Home 
</button>