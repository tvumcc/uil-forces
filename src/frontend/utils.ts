function pad(n: number) {
    return (n < 10 ? '0' : '') + n;
}

export function getTzOffset() {
    let tzOffset = -(new Date().getTimezoneOffset())
    let diff = tzOffset >= 0 ? "+" : "-"

    return diff + pad(Math.floor(Math.abs(tzOffset) / 60)) + ":" + pad(Math.abs(tzOffset) % 60)
}

export function toTzIsoString(date: Date): string {
    return date.getFullYear() +
        '-' + pad(date.getMonth() + 1) +
        '-' + pad(date.getDate()) +
        'T' + pad(date.getHours()) +
        ':' + pad(date.getMinutes()) +
        ':' + pad(date.getSeconds())
}