let toasts: Toast[] = $state([])
let toastIDCounter = 0;

export enum ToastType {
    Success = "success",
    Info = "info",
    Error = "error"
}

export interface Toast {
    message: string,
    id: number,
    type: ToastType,
}

export function getToasts(): Toast[] {
    return toasts
}

export function addToast(message: string, type: ToastType = ToastType.Success, duration_ms: number = 4000) {
    const id = toastIDCounter++;
    toasts.push({message, id, type})

    console.log(`adding toast ${id} "${message}"`)

    if (duration_ms > 0) {
        setTimeout(() => dismissToast(id), duration_ms)
    }
}

export function dismissToast(id: number) {
    const idx = toasts.findIndex((t) => t.id === id) 
    if (idx !== 1) toasts.splice(idx, 1)
}