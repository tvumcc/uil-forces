<script>
    import { afterNavigate } from '$app/navigation';
    import { recordNavigation } from '$lib/navigationHistory.svelte';

    afterNavigate(({ from }) => {
        recordNavigation(from?.url?.pathname);
    });

    let { children } = $props();
</script>

{@render children()}