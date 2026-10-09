/**
 * SomaAgent01 — chat attachment upload against filesv2 only.
 *
 * Endpoints are exactly the ones declared in `admin/filesv2/api.py`:
 *
 *   POST /api/v2/filesv2/upload            → {file_id, upload_url, expires_in}
 *     • AWS configured  → `upload_url` is a presigned S3 PUT (absolute URL)
 *     • fallback        → `upload_url` is this deployment's own
 *                         /api/v2/filesv2/upload-local/{file_id} (multipart)
 *
 * `tenant_id` and `user_id` are required query parameters of POST /upload.
 * They are read from GET /api/v2/auth/me — never invented client-side.
 *
 * A file that does not upload gets NO `file_id`. The message still carries
 * name/type/size so the card renders, and the failure is reported on the
 * message itself.
 */
import { apiClient, ApiError } from './api-client.js';

export interface AttachmentMeta {
    name: string;
    type: string;
    size: number;
    /** filesv2 file id — present only after the bytes were accepted. */
    file_id?: string;
}

export interface AttachmentUploadFailure {
    name: string;
    reason: string;
}

interface UploadTicket {
    file_id: string;
    upload_url: string;
    expires_in: number;
}

interface AuthMe {
    id: string;
    tenant_id?: string | null;
}

interface UploadIdentity {
    tenantId: string;
    userId: string;
}

let identityPromise: Promise<UploadIdentity> | null = null;

function loadIdentity(): Promise<UploadIdentity> {
    if (!identityPromise) {
        identityPromise = apiClient
            .get<AuthMe>('/auth/me')
            .then((me) => {
                const tenantId = (me?.tenant_id ?? '').trim();
                const userId = (me?.id ?? '').trim();
                if (!tenantId || !userId) {
                    throw new Error(
                        'this session has no tenant_id/user_id — filesv2 upload requires both',
                    );
                }
                return { tenantId, userId };
            })
            .catch((err: unknown) => {
                // Never cache a failure: the next send retries cleanly.
                identityPromise = null;
                if (err instanceof Error && err.message) throw err;
                throw new Error('identity unavailable (GET /api/v2/auth/me failed)');
            });
    }
    return identityPromise;
}

function reasonOf(err: unknown): string {
    if (err instanceof ApiError) {
        if (!err.status) return err.message || 'network error — request never reached the API';
        return `${err.message || 'request failed'} (HTTP ${err.status})`;
    }
    if (err instanceof Error && err.message) return err.message;
    return 'upload failed';
}

async function putBytes(ticket: UploadTicket, file: File, mime: string): Promise<void> {
    if (/^https?:\/\//i.test(ticket.upload_url)) {
        // Presigned S3 PUT: the signature covers bucket/key/Content-Type,
        // so the header must be the same mime string sent to /upload.
        const res = await fetch(ticket.upload_url, {
            method: 'PUT',
            headers: { 'Content-Type': mime },
            body: file,
        });
        if (!res.ok) {
            throw new Error(`presigned PUT rejected (HTTP ${res.status})`);
        }
        return;
    }

    // AAAS-in-a-box: the API handed back its own multipart endpoint.
    const form = new FormData();
    form.append('file', file, file.name);
    const res = await fetch(ticket.upload_url, {
        method: 'POST',
        body: form,
        credentials: 'include',
    });
    if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: unknown; detail?: unknown };
        const detail =
            typeof body.error === 'string'
                ? body.error
                : typeof body.detail === 'string'
                    ? body.detail
                    : '';
        throw new Error(detail ? `upload rejected: ${detail}` : `upload rejected (HTTP ${res.status})`);
    }
}

/** Upload one file through POST /filesv2/upload + its returned upload_url. */
export async function uploadAttachment(file: File): Promise<AttachmentMeta> {
    const mime = file.type || 'application/octet-stream';
    const { tenantId, userId } = await loadIdentity();
    const qs = new URLSearchParams({
        filename: file.name,
        mime_type: mime,
        size_bytes: String(file.size),
        tenant_id: tenantId,
        user_id: userId,
    });
    const ticket = await apiClient.request<UploadTicket>('POST', `/filesv2/upload?${qs.toString()}`);
    if (!ticket?.file_id || !ticket.upload_url) {
        throw new Error('POST /filesv2/upload returned no file_id/upload_url');
    }
    await putBytes(ticket, file, mime);
    return { name: file.name, type: mime, size: file.size, file_id: ticket.file_id };
}

/**
 * Upload every attachment. Never throws: `results` aligns 1:1 with `files`
 * (a failed file keeps name/type/size but no `file_id`), and `failures`
 * carries one honest reason per failed file.
 */
export async function uploadAttachments(
    files: File[],
): Promise<{ results: AttachmentMeta[]; failures: AttachmentUploadFailure[] }> {
    const results: AttachmentMeta[] = [];
    const failures: AttachmentUploadFailure[] = [];
    for (const file of files) {
        try {
            results.push(await uploadAttachment(file));
        } catch (err) {
            results.push({
                name: file.name,
                type: file.type || 'application/octet-stream',
                size: file.size,
            });
            failures.push({ name: file.name, reason: reasonOf(err) });
        }
    }
    return { results, failures };
}
