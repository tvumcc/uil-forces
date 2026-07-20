<script lang="ts">
    interface AdminLink {
        href: string
        label: string
        description: string
    }

    const links: AdminLink[] = [
        { href: "/admin/users",       label: "Users",        description: "Add and view user accounts" },
        { href: "/admin/contests",    label: "Contests",     description: "Schedule and organize contests" },
        { href: "/admin/psets",       label: "Problem Sets", description: "Create and edit problem sets" },
        { href: "/admin/submissions", label: "Submissions",  description: "Review, rejudge, and delete graded submissions" },
        { href: "/admin/settings",    label: "Settings",     description: "Site-wide configuration and grading options" },
    ]
</script>

<div class="main-container">
    <header class="hero">
        <h1>Admin Home</h1>
        <p class="subtitle">Manage contests, problem sets, users, and site settings</p>
    </header>

    <div class="admin-grid">
        {#each links as link}
            <a href={link.href} class="admin-card">
                <span class="card-label">{link.label}</span>
                <p class="card-description">{link.description}</p>
            </a>
        {/each}
    </div>
</div>

<style>
    .admin-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 14px;
    }
    @media (max-width: 700px) {
        .admin-grid { grid-template-columns: 1fr; }
    }

    .admin-card {
        display: block;
        background-color: #0b1220;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 16px 18px;
        text-decoration: none;
        color: white;
        transition: border-color 0.15s ease, background-color 0.15s ease;
    }
    .admin-card:hover {
        border-color: #00d492;
        background-color: #0d1626;
    }
    @media (prefers-reduced-motion: reduce) {
        .admin-card { transition: none; }
    }

    .card-label {
        font-weight: bold;
        font-size: 15px;
        color: #00d492;
    }
    .card-description {
        margin: 6px 0 0 0px;
        font-size: 13px;
        color: #64748b;
    }
</style>