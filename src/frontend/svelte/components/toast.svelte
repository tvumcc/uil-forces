<script lang="ts">
    import {getToasts, dismissToast} from "../../toastStore.svelte"
    import {fly, fade} from "svelte/transition"

    const toasts = getToasts()
</script>

<div class="toast-container">
  {#each toasts as toast (toast.id)}
    <button
      class="toast {toast.type}"
      in:fly={{ x: 100, duration: 300 }}
      out:fade={{ duration: 200 }}
      onclick={() => dismissToast(toast.id)}
    >
      {toast.message}
    </button>
  {/each}
</div>

<style>
  .toast-container {
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    z-index: 9999;
  }

  .toast {
    padding: 0.75rem 1.25rem;
    border-radius: 2px;
    color: white;
    font-size: 0.9rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    cursor: pointer;
    min-width: 200px;
    max-width: 320px;
  }

  .success { background: #22c55e; }
  .error   { background: #ef4444; }
  .info    { background: #3b82f6; }
</style>