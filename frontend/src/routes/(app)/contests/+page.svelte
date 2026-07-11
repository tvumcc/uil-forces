<script lang="ts">
    import MenuBar from "$lib/menuBar.svelte"
    import type {Contest} from "$lib/utils"
    import { addToast, ToastType } from "$lib/toastStore.svelte";
    import { goto } from "$app/navigation";

    let pastContests: Contest[] = $state([])
    let ongoingContests: Contest[] = $state([])
    let upcomingContests: Contest[] = $state([])

    async function getData() {
        let response: Response = await fetch("/api/contests")
        let data = await response.json()

        if (!response.ok) {
            addToast("Internal Error", ToastType.Error)
            goto("/")
            return
        }

        pastContests = data.past
        ongoingContests = data.ongoing
        upcomingContests = data.upcoming
    }
</script>

<MenuBar />
<div class="main-container">
    <h1>Contests</h1>

    {#await getData()}
        <p>Loading...</p>
    {:then}
        {#if ongoingContests.length + upcomingContests.length + pastContests.length === 0}
            <p>There are no contests to display</p>
        {/if}

        {#if ongoingContests.length > 0}
            <h2>Ongoing Contests</h2>
            {#each ongoingContests as contest}
                <a href="/contest?id={contest.id}">{contest.name}</a><br>
            {/each}
        {/if}

        {#if upcomingContests.length > 0}
            <h2>Upcoming Contests</h2>
            {#each upcomingContests as contest}
                <a href="/contest?id={contest.id}">{contest.name}</a><br>
            {/each}
        {/if}

        {#if pastContests.length > 0}
            <h2>Past Contests</h2>
            {#each pastContests as contest}
                <a href="/contest?id={contest.id}">{contest.name}</a><br>
            {/each}
        {/if}
    {/await}
</div>