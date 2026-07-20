<script lang="ts">
    import { goto } from "$app/navigation";
    import { page } from "$app/state";
    import type { User } from "$lib/utils"
    import { addErrorToast } from "./toastStore.svelte";

    interface MenuBarProps {
        user: User
    }

    let { user }: MenuBarProps = $props()

    async function logout(event: Event) {
        event.preventDefault()
        const response: Response = await fetch("/api/logout")
        if (!response.ok) {
            await addErrorToast(response, "Failed to log out")
            return
        }
        goto("/login")
    }
</script>

<div class="menu-bar">
    <div id="links">
        <a href="/" class="brand">UIL Forces</a>
        <a class="link" class:active={page.url.pathname === "/"} href="/">Home</a>
        <a class="link" class:active={page.url.pathname.startsWith("/contest")} href="/contests">Contests</a>
        {#if user !== undefined && user.isAdmin}
            <a class="link" class:active={page.url.pathname.startsWith("/admin")} href="/admin">Admin</a>
        {/if}
    </div>
    <div id="user-info">
        <span id="username">{user.username}</span>
        {#if user.isAdmin}
            <span class="badge badge-admin">Admin</span>
        {/if}
        <span class="divider">|</span>
        <a class="link" href="/" onclick={logout}>Log out</a>
    </div>
</div>

<style>
    .menu-bar {
        box-sizing: border-box;
        background-color: #101828;
        padding: 20px 25px;
        border-radius: 10px;
        margin: 10px 0px;
        width: 95%;
        max-width: 1000px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        align-items: center;
        flex: 0 0 auto;
    }

    #links {
        display: flex;
        justify-content: left;
        align-items: center;
        gap: 22px;
    }

    #user-info {
        display: flex;
        justify-content: right;
        align-items: center;
        gap: 10px;
    }

    .brand {
        font-size: 15px;
        font-weight: bold;
        color: white;
        text-decoration: none;
        margin-right: 6px;
    }

    #username {
        font-size: 14px;
        color: #cbd5e1;
    }

    .divider {
        color: #334155;
        font-size: 14px;
    }

    .link {
        text-decoration: none;
        font-weight: bold;
        font-size: 14px;
        color: #94a3b8;
        transition: color 0.15s ease;
    }
    .link:hover {
        color: #00d492;
    }
    .link.active {
        color: #00d492;
    }
    @media (prefers-reduced-motion: reduce) {
        .link { transition: none; }
    }
</style>