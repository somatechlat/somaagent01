// Deprecated legacy module: forward to unified SSE notifications store
import { store as notificationsSse } from "/components/notifications/notificationsStore.js";
export const store = notificationsSse;
export default { store };
