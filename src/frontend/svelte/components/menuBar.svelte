<script lang="ts">
    async function get_user() {
        let response: Response = await fetch("/api/user")
        let json = await response.json()
        return json
    }

    async function logout(event: Event) {
        event.preventDefault()
        let response: Response = await fetch("/api/logout")
        let json = await response.json()        
        window.location.href = json["redirect"]
    }

    let userPromise = get_user()
</script>

<style>
    @import "../../style.css";

    .menu-bar {
        box-sizing: border-box;
        background-color: #101828;
        padding: 20px 25px;
        border-radius: 10px;
        margin: 10px 0px;
        width: 95%;
        max-width: 1000px;
        min-height: 1vh;

        display: grid;
        grid-template-columns: 1fr 1fr; 
        flex: 0 0 auto;
    }

    #links {
        display: flex;
        justify-content: left;
        align-items: center;
        gap: 20px;
        text-decoration: none;
    }

    #user-info {
        display: flex;
        justify-content: right;
        align-items: center;
        gap: 5px;
    }

    p, h1, a {
        margin: 0;
        font-size: 15px;
    }

    .link {
        text-decoration: none;
        font-weight: bold;
    }
</style>

<div class="menu-bar">
    <div id="links">
        <h1>UIL Forces</h1>
        <a class="link" href="/">Home</a>
        <a class="link" href="/contests">Contests</a>
        <a class="link" href="/psets">Practice</a>
    </div>
    <div id="user-info">
        {#await userPromise then user}
            <p id="username">{user.username}</p>
        {/await}
        <p>|</p>
        <a class="link" href="/" onclick={logout}>Log out</a>
    </div>
</div>