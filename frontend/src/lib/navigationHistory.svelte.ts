import { goto } from "$app/navigation"

let prevPath: string | null = $state(null)

export function recordNavigation(from: string | undefined) {
    if (from) prevPath = from
}

export function goBack() {
    if (prevPath) {
        goto(prevPath)
    } else {
        goto("/")
    }
}
