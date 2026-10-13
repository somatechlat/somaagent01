/**
 * Material icon names for file attachments — NO emojis (Soma UI law).
 * Shared by composer chips and message attachment cards.
 */
export function attachmentIcon(name: string, type?: string): string {
    const n = (name || '').toLowerCase();
    const t = (type || '').toLowerCase();

    // Images
    if (t.startsWith('image/') || /\.(png|jpe?g|gif|webp|avif|bmp|heic)$/.test(n)) return 'image';
    // PDF
    if (t === 'application/pdf' || n.endsWith('.pdf')) return 'picture_as_pdf';
    // Video / audio
    if (t.startsWith('video/') || /\.(mp4|webm|mov|mkv)$/.test(n)) return 'movie';
    if (t.startsWith('audio/') || /\.(mp3|wav|ogg|m4a|flac)$/.test(n)) return 'audio_file';
    // Archives
    if (/\.(zip|tar|gz|7z|rar)$/.test(n) || t.includes('zip') || t.includes('tar')) return 'folder_zip';
    // Word / docs
    if (/\.(docx?|odt|rtf)$/.test(n) || t.includes('word') || t.includes('opendocument.text')) {
        return 'article';
    }
    // Spreadsheets
    if (/\.(xlsx?|ods|xls)$/.test(n) || t.includes('sheet') || t.includes('excel')) {
        return 'table_chart';
    }
    // Slides
    if (/\.(pptx?|odp|pps)$/.test(n) || t.includes('presentation') || t.includes('powerpoint')) {
        return 'slideshow';
    }
    // Text / markup / data
    if (/\.(md|txt|csv|json|yml|yaml|toml|log)$/.test(n)) return 'description';
    // Source code
    if (/\.(py|js|ts|tsx|jsx|go|rs|java|kt|c|cpp|h|hpp|cs|rb|php|sh|sql)$/.test(n)) {
        return 'code';
    }
    // Fonts
    if (/\.(ttf|otf|woff2?)$/.test(n) || t.includes('font')) return 'font_download';
    // Generic binary
    return 'attach_file';
}

export function formatBytes(bytes: number): string {
    if (!Number.isFinite(bytes) || bytes < 0) return '—';
    if (bytes < 1024) return `${bytes} B`;
    const units = ['KB', 'MB', 'GB'];
    let v = bytes;
    let i = -1;
    do {
        v /= 1024;
        i += 1;
    } while (v >= 1024 && i < units.length - 1);
    return `${v.toFixed(v >= 10 ? 0 : 1)} ${units[i]}`;
}
