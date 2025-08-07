<script lang="ts">
    async function logout() {
        let response: Response = await fetch("/api/logout")
        let json = await response.json()        
        window.location.href = json["redirect"]
    }
</script>

<button onclick={logout}>
    Log out
</button>