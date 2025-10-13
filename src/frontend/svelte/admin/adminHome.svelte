<script lang="ts">
    import MenuBar from "../components/menuBar.svelte"
</script>

<style>
    @import "../../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Admin Home</h1>
    <h3><a href="/admin/settings">Settings</a></h3>
    <h3><a href="/admin/users">Users</a></h3>
    <h3><a href="/admin/contests">Contests</a></h3>
    <h3><a href="/admin/psets">Problem Sets</a></h3>
    <h3><a href="/admin/submissions">Submissions</a></h3>
</div>