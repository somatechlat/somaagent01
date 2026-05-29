/**
 * Simple i18n helper for frontend user-facing strings.
 * TODO: Replace with proper i18n framework (e.g. i18next) when localization is prioritized.
 */

export enum ErrorCode {
  INVALID_CREDENTIALS = 'invalid_credentials',
  FETCH_USER_INFO_FAILED = 'fetch_user_info_failed',
  LOGIN_FAILED = 'login_failed',
}

export enum SuccessCode {
  // Add success codes as needed
}

const MESSAGES: Record<string, string> = {
  [ErrorCode.INVALID_CREDENTIALS]: 'Invalid credentials',
  [ErrorCode.FETCH_USER_INFO_FAILED]: 'Failed to fetch user info',
  [ErrorCode.LOGIN_FAILED]: 'Login failed',
};

export function getMessage(code: string, ...args: unknown[]): string {
  let msg = MESSAGES[code] || code;
  // Simple positional replacement using {0}, {1}, etc.
  args.forEach((arg, index) => {
    msg = msg.replace(`{${index}}`, String(arg));
  });
  return msg;
}
