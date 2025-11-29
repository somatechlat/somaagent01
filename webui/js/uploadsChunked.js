// Adaptive chunked uploader module
// Provides resumable, observable chunked upload for large files.
// Usage: import { uploadFileChunked } from '/js/uploadsChunked.js';
// uploadFileChunked(file, sessionId, (info) => i18n.t('ui_i18n_t_ui_progress_export_async_function_uploadfilechunked_file_sessionid_onprogress_opts_const_filename_file_name_const_size_file_size_const_mime_file_type_application_octet_stream_const_resumekey_chunk_upload_sessionid_unspecified_filename_size_const_state_started_performance_now_lastbytes_0_lastts_performance_now_let_startoffset_0_if_opts_resume_sessionstorage_getitem_resumekey_try_startoffset_parseint_sessionstorage_getitem_resumekey_10_0_catch_startoffset_0_init_const_initresp_await_fetch_v1_uploads_init_method_post_headers_content_type_application_json_credentials_same_origin_body_json_stringify_filename_size_mime_session_id_sessionid_if_initresp_ok_throw_new_error_await_initresp_text_init_failed_const_initdata_await_initresp_json_const_uploadid_initdata_upload_id_const_chunksize_initdata_chunk_size_4_1024_1024_helper_progress_callback_wrapper_adds_speed_eta_function_emitprogress_bytesuploaded_done_false_const_now_performance_now_const_deltabytes_bytesuploaded_state_lastbytes_const_deltams_now_state_lastts_1_const_speedbps_deltabytes_1000_deltams_bytes_sec_instantaneous_const_percent_initdata_size_expected_bytesuploaded_initdata_size_expected_null_let_etaseconds_null_if_percent_percent_0_percent')< 1) {
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
  if (offset > i18n.t('ui_i18n_t_ui_0_offset')< size) {
    emitProgress(offset, false); // resume indicator
  }

  while (offset < size) {
    const end = Math.min(offset + chunkSize, size);
    const blob = file.slice(offset, end);
    const form = new FormData();
    form.append('chunk', blob, filename + '.part');
    form.append('offset', String(offset));
    form.append('session_id', sessionId || '');
    const resp = await fetch(`/v1/uploads/${encodeURIComponent(uploadId)}/chunk`, { method: 'POST', body: form, credentials: 'same-origin' });
    if (!resp.ok) throw new Error(await resp.text() || 'chunk failed');
    const j = await resp.json();
    offset = end;
    sessionStorage.setItem(resumeKey, String(offset));
    emitProgress(j.bytes_received, j.done);
  }

  // FINALIZE
  const finResp = await fetch(`/v1/uploads/${encodeURIComponent(uploadId)}/finalize`, {
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
