// Deprecated prior module: forward to unified SSE notifications store
import { store as notificationsSse } from "./notificationsStore.js";
export const store = notificationsSse;
export default { store };
