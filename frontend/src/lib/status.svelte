<script lang="ts">
    import { statusStr } from "$lib/utils"

    let { statusCode, fitText = true }: { statusCode: number, fitText?: boolean } = $props()

    // Maps each status index to a semantic variant, rather than relying on numeric CSS classes
    const variants = ["pending", "accepted", "failed", "failed", "failed", "failed", "failed"]
</script>

<span
    class="status-badge status-{variants[statusCode] ?? "pending"}"
    class:inline={fitText}
    class:block={!fitText}
>
    <span class="dot"></span>
    {statusStr[statusCode] ?? "Unknown"}
</span>

<style>
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
    }
    .status-badge.block {
        display: flex;
        width: fit-content;
    }

    .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .status-pending {
        background-color: rgba(100, 116, 139, 0.15);
        color: #94a3b8;
    }
    .status-pending .dot {
        background-color: #64748b;
    }

    .status-accepted {
        background-color: rgba(0, 212, 146, 0.15);
        color: #00d492;
    }
    .status-accepted .dot {
        background-color: #00d492;
    }

    .status-failed {
        background-color: rgba(248, 113, 113, 0.15);
        color: #f87171;
    }
    .status-failed .dot {
        background-color: #f87171;
    }
</style>