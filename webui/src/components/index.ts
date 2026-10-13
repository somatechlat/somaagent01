// ── Peer chrome modules (side-effect custom-element registration) ──────────
// Only modules that actually exist are imported. Missing peers are listed
// below as comments — no stubs, no placeholders, no fakes (SOMA LAW).

// toast
import './soma-toast-stack.js';
export { SomaToastStack, pushToast } from './soma-toast-stack.js';
export type { SomaToastDetail, SomaToastItem, SomaToastAction, SomaToastKind } from './soma-toast-stack.js';

// bell
import './soma-notification-bell.js';
export { SomaNotificationBell } from './soma-notification-bell.js';

// tray
import './soma-notification-tray.js';
export { SomaNotificationTray } from './soma-notification-tray.js';
export type { SomaNotification, SomaNotificationLoadState } from './soma-notification-tray.js';

// profile
import './soma-user-profile-card.js';
export { SomaUserProfileCard } from './soma-user-profile-card.js';
export type { UserProfileData } from './soma-user-profile-card.js';

// password-modal
import './soma-password-modal.js';
import './soma-profile-modal.js';
export { SomaProfileModal } from './soma-profile-modal.js';
export { SomaPasswordModal } from './soma-password-modal.js';

// notification-center
import './soma-notification-center.js';
export { SomaNotificationCenter } from './soma-notification-center.js';

// agent-hands
import './soma-agent-hands.js';
export { SomaAgentHands } from './soma-agent-hands.js';
import './soma-tool-policy-modal.js';
export { SomaToolPolicyModal } from './soma-tool-policy-modal.js';

// brain-manager
import './soma-brain-manager.js';
export { SomaBrainManager } from './soma-brain-manager.js';

// artifacts
import './soma-artifacts.js';
export { SomaArtifacts } from './soma-artifacts.js';

// file-manager
import './soma-file-manager.js';
import './soma-file-manager-modal.js';
export { SomaFileManagerModal } from './soma-file-manager-modal.js';
export { SomaFileManager } from './soma-file-manager.js';
export type { FileOut, FileListResponse, FileListResponseEnvelope, FileManagerMode } from './soma-file-manager.js';

// chat-settings
import './soma-chat-settings.js';
export { SomaChatSettings } from './soma-chat-settings.js';

// reasoning-block
import './soma-reasoning-block.js';
export { SomaReasoningBlock, REASONING_FORMATS, REASONING_MODES } from './soma-reasoning-block.js';
export type { ReasoningFormat, ReasoningMode } from './soma-reasoning-block.js';

// All target peers have landed and are registered above.

// ── Core components ───────────────────────────────────────────────────────

export { SomaButton } from './soma-button.js';
export { SomaSelect } from './soma-select.js';
export { SomaToggle } from './soma-toggle.js';
export { SomaGlassModal as SomaModal } from './soma-glass-modal.js'; // Mapping SomaModal to GlassModal

export { SomaGlassModal } from './soma-glass-modal.js';
export { SomaStatusBadge } from './soma-status-badge.js';
export { SomaActionMenu } from './soma-action-menu.js';
export { SomaDataTable } from './soma-data-table.js';
export { SomaFormField } from './soma-form-field.js';
export { SomaPermissionGuard } from './soma-permission-guard.js';
export { SomaSidebar } from './soma-sidebar.js';
export { SomaStatCard } from './soma-stat-card.js';
export { SettingsForm } from './settings-form.js';

// Workspace Components (Agent Zero inspired)
export { SomaAgentHeader } from './soma-agent-header.js';
export { SomaComposer } from './soma-composer.js';
export { SomaComposerMenu } from './soma-composer-menu.js';
export { SomaWelcomeDashboard } from './soma-welcome-dashboard.js';
export { SomaRightPanel } from './soma-right-panel.js';
export { SomaCapsuleEditor } from './soma-capsule-editor.js';

// Chat E2E (C2–C4): message bubble, tool timeline, topbar controls
export { SomaMessage } from './soma-message.js';
export { SomaToolTimeline } from './soma-tool-timeline.js';
export { SomaChatTopbar } from './soma-chat-topbar.js';
export { SomaStatusDot } from './soma-status-dot.js';
export type { ToolCallStep, ToolStepStatus } from './soma-tool-timeline.js';
export type { ComposerSendDetail } from './soma-composer.js';
export type { ChatControlAction } from './soma-chat-topbar.js';

// Types
export type { SelectOption } from './soma-select.js';
