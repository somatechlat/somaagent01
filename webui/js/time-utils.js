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
  if (!utcIsoString) return ''i18n.t('ui_i18n_t')'ui_const_date_new_date_utcisostring_const_defaultoptions_datestyle')'i18n.t('ui_medium')'i18n.t('i18n.t('ui_timestyle')')'i18n.t('ui_medium')'i18n.t('i18n.t('ui_return_new_intl_datetimeformat_undefined_use_browser')')'i18n.t('ui_s_locale_defaultoptions_options_format_date_convert_a_local_date_object_to_utc_iso_string_param_date_date_date_object_in_local_time_returns_string_utc_iso_string_export_function_toutcisostring_date_if_date_return')''i18n.t('ui_i18n_t')'ui_return_date_toisostring_get_current_time_as_utc_iso_string_returns_string_current_utc_time_in_iso_format_export_function_getcurrentutcisostring_return_new_date_toisostring_format_a_utc_iso_string_for_display_in_local_time_with_configurable_format_param_string_utcisostring_utc_time_in_iso_format_param_string_format_format_type')'i18n.t('ui_full')'i18n.t('i18n.t('ui_ui')')'i18n.t('ui_date')'i18n.t('i18n.t('ui_ui')')'i18n.t('ui_time')'i18n.t('i18n.t('ui_ui')')'i18n.t('ui_short')'i18n.t('i18n.t('ui_returns_string_formatted_local_time_string_export_function_formatdatetime_utcisostring_format')')'i18n.t('ui_full')'i18n.t('i18n.t('ui_if_utcisostring_return')')''i18n.t('ui_i18n_t')'ui_const_date_new_date_utcisostring_const_formatoptions_full_datestyle')'i18n.t('ui_medium')'i18n.t('i18n.t('ui_timestyle')')'i18n.t('ui_medium')'i18n.t('i18n.t('ui_date_datestyle')')'i18n.t('ui_medium')'i18n.t('i18n.t('ui_time_timestyle')')'i18n.t('ui_medium')'i18n.t('i18n.t('ui_short_datestyle')')'i18n.t('ui_short')'i18n.t('i18n.t('ui_timestyle')')'i18n.t('ui_short')'i18n.t('i18n.t('ui_return_tolocaltime_utcisostring_formatoptions_format_formatoptions_full_get_the_user')')'i18n.t('ui_s_local_timezone_name_returns_string_timezone_name_e_g')'i18n.t('i18n.t('ui_america_new_york')')')
 */
export function getUserTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}
