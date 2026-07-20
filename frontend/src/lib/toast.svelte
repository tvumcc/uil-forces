<script lang="ts">
  import {getToasts, dismissToast} from "$lib/toastStore.svelte"
  import {fly, fade} from "svelte/transition"
  const toasts = getToasts()
</script>

<div class="toast-container">
  {#each toasts as toast (toast.id)}
    <button
      class="toast toast-{toast.type}"
      in:fly={{ x: 60, duration: 250 }}
      out:fade={{ duration: 200 }}
      onclick={() => dismissToast(toast.id)}
    >
      <span class="dot"></span>
      <span class="message">{toast.message}</span>
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
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.7rem 1.1rem;
    border-radius: 8px;
    background-color: #101828;
    border: 1px solid #1e293b;
    color: white;
    font-family: inherit;
    font-size: 0.85rem;
    text-align: left;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
    cursor: pointer;
    min-width: 220px;
    max-width: 340px;
  }
  .toast:hover {
    border-color: #334155;
  }

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .message {
    flex: 1;
  }

  .toast-success .dot { background-color: #00d492; }
  .toast-error   .dot { background-color: #f87171; }
  .toast-info    .dot { background-color: #60a5fa; }
</style>