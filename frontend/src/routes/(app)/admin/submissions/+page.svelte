<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/state"
    import { goBack } from "$lib/navigationHistory.svelte";
    import SubmissionTable from "$lib/submissionTable.svelte";
    import { addErrorToast } from "$lib/toastStore.svelte";
    import type { Submission } from "$lib/utils"

    let pageNum: number = $derived(Number(page.url.searchParams.get("page") ?? "1"))
    let submissions: Submission[] = $state([])
    let loading = $state(true)

    async function getData(p: number) {
        loading = true
        const response: Response = await fetch(`/api/admin/submissions/${p}`)
        if (!response.ok) {
            await addErrorToast(response, "Failed to load submissions list")
            goBack()
            return
        }
        const data = await response.json()
        submissions = data.submissions
        loading = false
    }

    $effect(() => {
        getData(pageNum)
    })
</script>

<div class="main-container wide">
    <header class="hero">
        <h1>All Submissions</h1>
    </header>

    {#if loading}
        <div class="panel skeleton"></div>
    {:else}
        <section class="panel">
            <div class="pager">
                {#if pageNum > 1}
                    <a href={`/admin/submissions?page=${pageNum - 1}`}>← Previous</a>
                {:else}
                    <span class="pager-disabled">← Previous</span>
                {/if}
                <span class="page-indicator">Page {pageNum}</span>
                {#if submissions.length === 50}
                    <a href={`/admin/submissions?page=${pageNum + 1}`}>Next →</a>
                {:else}
                    <span class="pager-disabled">Next →</span>
                {/if}
            </div>
            <SubmissionTable {submissions} showUsers={true} showActions={true} />
        </section>
    {/if}
</div>

<style>
    .pager {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
        font-size: 13px;
    }
    .page-indicator {
        color: #64748b;
    }
    .pager-disabled {
        color: #334155;
    }
</style>