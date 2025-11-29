// Stream Status Banner: shows SSE connectivity state using event-bus
import * as bus from "i18n.t('ui_i18n_t_ui_js_event_bus_js')";

(function () {
  const ID = 'stream-status-banner';
  const mounted = () => document.getElementBi18n.t('ui_document_getelementbyid_id_null_i18n_t_ui_document_getelementbyid_id_null_function_ensurestyles_if_document_getelementbyid_stream_status_styles_return_const_css_stream_status_banner_position_fixed_bottom_12px_left_12px_z_index_9999_font_size_12px_stream_status_banner_bubble_display_inline_flex_gap_6px_align_items_center_padding_6px_10px_border_radius_16px_box_shadow_0_2px_6px_rgba_0_0_0_0_15_background_111827_color_e5e7eb_stream_status_banner_online_bubble_background_065f46_color_ecfdf5_stream_status_banner_reconnecting_bubble_background_92400e_color_fff7ed_stream_status_banner_stale_bubble_background_1e3a8a_color_dbeafe_stream_status_banner_offline_bubble_background_7f1d1d_color_fef2f2_stream_status_banner_dot_width_8px_height_8px_border_radius_50_background_currentcolor_opacity_0_9_stream_status_banner_msg_opacity_0_95_const_style_document_createelement_style_style_id_stream_status_styles_style_textcontent_css_document_head_appendchild_style_function_mount_if_mounted_return_ensurestyles_const_el_document_createelement_div_el_id_id_el_classname_stream_status_banner_offline_el_innerhtml_class_i18n_t_ui_dot')an class="i18n.t('ui_i18n_t_ui_msg')">i18n.t('ui_i18n_t_ui_connecting')</span></div>`;
    document.body.appendChild(el);
  }

  function setState(state, text) {
    const el = document.getElementById(ID);
    if (!el) return;
    el.className = `stream-status-banner ${state}`;
    const msg = el.querySelector('.msg');
    if (msg && text) msg.textContent = text;
  }

  function init() {
    mount();
    let hideTimer = null;

    bus.on('stream.online', () => {
      setState('online', 'Live');
      if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
      hideTimer = setTimeout(() => {
        const el = document.getElementById(ID);
        if (el) el.style.display = 'none';
      }, 1500);
    });

    bus.on('stream.offline', (p) => {
      const el = document.getElementById(ID);
      if (el) el.style.display = '';
      const reason = (p && (p.reason || p.error)) ? `: ${String(p.reason || p.error)}` : '';
      setState('offline', `Disconnected${reason}`);
    });

    bus.on('stream.reconnecting', (p) => {
      const el = document.getElementById(ID);
      if (el) el.style.display = '';
      const attempt = p && typeof p.attempt === 'number' ? p.attempt : 1;
      const delay = p && typeof p.delay === 'number' ? p.delay : 0;
      setState('reconnecting', `Reconnecting (attempt ${attempt}, ${delay}ms)…`);
    });

    bus.on('stream.stale', (p) => {
      const el = document.getElementById(ID);
      if (el) el.style.display = '';
      const ms = p && p.ms_since_heartbeat ? p.ms_since_heartbeat : '?';
      setState('stale', `Stale (${ms}ms since heartbeat)`);
    });

    bus.on('stream.retry.success', (p) => {
      // transient success indicator if banner currently visible in reconnect state
      const el = document.getElementById(ID);
      if (el && el.style.display !== 'none') {
        setState('online', 'Recovered');
        setTimeout(() => {
          if (el) el.style.display = 'none';
        }, 1200);
      }
    });

    bus.on('stream.retry.giveup', (p) => {
      const el = document.getElementById(ID);
      if (el) el.style.display = '';
      setState('offline', 'Give up (manual reload)');
    });

    // heartbeat keeps online state sticky
    bus.on('stream.heartbeat', () => {
      // Keep banner hidden if stable
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
