// Adaptive chunked uploader module
// Provides resumable, observable chunked upload for large files.
// Usage: import { uploadFileChunked } from '/js/uploadsChunked.js';
// uploadFileChunked(file, sessionId, (info) => { /* progress */ })

import { API } from "/static/config.js";

export async function uploadFileChunked(file, sessionId, onProgress = () => {}, opts = {}) {
  const filename = file.name;
  const size = file.size;
  const mime = file.type || 'application/octet-stream';
  const resumeKey = `chunk-upload:${sessionId || 'unspecified'}:${filename}:${size}`;
  const state = { started: performance.now(), lastBytes: 0, lastTs: performance.now() };
  let startOffset = 0;
  if (opts.resume && sessionStorage.getItem(resumeKey)) {
    try { startOffset = parseInt(sessionStorage.getItem(resumeKey), 10) || 0; } catch (_) { startOffset = 0; }
  }

  // INIT
  const initResp = await fetch(`${API.BASE}${API.UPLOADS}/init`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ filename, size, mime, session_id: sessionId })
  });
  if (!initResp.ok) throw new Error(await initResp.text() || 'init failed');
  const initData = await initResp.json();
  const uploadId = initData.upload_id;
  const chunkSize = initData.chunk_size || (4 * 1024 * 1024);

  // Helper: progress callback wrapper (adds speed/eta)
  function emitProgress(bytesUploaded, done = false) {
    const now = performance.now();
    const deltaBytes = bytesUploaded - state.lastBytes;
    const deltaMs = now - state.lastTs || 1;
    const speedBps = deltaBytes * 1000 / deltaMs; // bytes/sec instantaneous
    const percent = initData.size_expected ? (bytesUploaded / initData.size_expected) : null;
    let etaSeconds = null;
    if (percent && percent > 0 && percent < 1) {
      etaSeconds = ((initData.size_expected - bytesUploaded) / (speedBps || 1));
    }
    state.lastBytes = bytesUploaded; state.lastTs = now;
    onProgress({
      filename,
      uploadId,
      bytesUploaded,
      bytesTotal: initData.size_expected,
      percent,
      speedBps,
      etaSeconds,
      mode: 'chunked',
      done
    });
  }

  // CHUNKS
  let offset = startOffset;
  if (offset > 0 && offset < size) {
    emitProgress(offset, false); // resume indicator
  }

  while (offset < size) {
    const end = Math.min(offset + chunkSize, size);
    const blob = file.slice(offset, end);
    const form = new FormData();
    form.append('chunk', blob, filename + '.part');
    form.append('offset', String(offset));
    form.append('session_id', sessionId || '');
    const resp = await fetch(`${API.BASE}${API.UPLOADS}/${encodeURIComponent(uploadId)}/chunk`, { method: 'POST', body: form, credentials: 'same-origin' });
    if (!resp.ok) throw new Error(await resp.text() || 'chunk failed');
    const j = await resp.json();
    offset = end;
    sessionStorage.setItem(resumeKey, String(offset));
    emitProgress(j.bytes_received, j.done);
  }

  // FINALIZE
  const finResp = await fetch(`${API.BASE}${API.UPLOADS}/${encodeURIComponent(uploadId)}/finalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ session_id: sessionId })
  });
  if (!finResp.ok) throw new Error(await finResp.text() || 'finalize failed');
  const descriptor = await finResp.json();
  emitProgress(size, true);
  sessionStorage.removeItem(resumeKey);
  return descriptor;
}

// Utility to compute a SHA-256 hash of a File incrementally using Web Crypto.
export async function hashFileSHA256(file, chunkSize = 4 * 1024 * 1024) {
  const sha = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
  return Array.from(new Uint8Array(sha)).map(b => b.toString(16).padStart(2, '0')).join('');
}
