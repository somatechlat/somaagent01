/**
 * Time utilities for handling UTC to local time conversion
 */

/**
 * Convert a UTC ISO string to a local time string
 * @param {string} utcIsoString - UTC time in ISO format
 * @param {Object} options - Formatting options for Intl.DateTimeFormat
 * @returns {string} Formatted local time string
 */
export function toLocalTime(utcIsoString, options = {}) {
  if (!utcIsoString) return ''i18n.t('ui_const_date_new_date_utcisostring_const_defaultoptions_datestyle')'medium'i18n.t('ui_timestyle')'medium'i18n.t('ui_return_new_intl_datetimeformat_undefined_use_browser')'s locale
    { ...defaultOptions, ...options }
  ).format(date);
}

/**
 * Convert a local Date object to UTC ISO string
 * @param {Date} date - Date object in local time
 * @returns {string} UTC ISO string
 */
export function toUTCISOString(date) {
  if (!date) return ''i18n.t('ui_return_date_toisostring_get_current_time_as_utc_iso_string_returns_string_current_utc_time_in_iso_format_export_function_getcurrentutcisostring_return_new_date_toisostring_format_a_utc_iso_string_for_display_in_local_time_with_configurable_format_param_string_utcisostring_utc_time_in_iso_format_param_string_format_format_type')'full'i18n.t('ui_')'date'i18n.t('ui_')'time'i18n.t('ui_')'short'i18n.t('ui_returns_string_formatted_local_time_string_export_function_formatdatetime_utcisostring_format')'full'i18n.t('ui_if_utcisostring_return')''i18n.t('ui_const_date_new_date_utcisostring_const_formatoptions_full_datestyle')'medium'i18n.t('ui_timestyle')'medium'i18n.t('ui_date_datestyle')'medium'i18n.t('ui_time_timestyle')'medium'i18n.t('ui_short_datestyle')'short'i18n.t('ui_timestyle')'short'i18n.t('ui_return_tolocaltime_utcisostring_formatoptions_format_formatoptions_full_get_the_user')'s local timezone name
 * @returns {string} Timezone name (e.g., 'i18n.t('ui_america_new_york')')
 */
export function getUserTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}
