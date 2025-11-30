import { createStore } from "/static/js/AlpineStore.js";
import * as Sleep from "/static/js/sleep.js";

const t = (k, fb) => (globalThis.i18n ? i18n.t(k) : fb || k);

// define the model object holding data and functions
const model = {
  isLoading: false,
  tunnelLink: "",
  linkGenerated: false,
  loadingText: "",
  qrCodeInstance: null,
  provider: "cloudflared",

  init() {
    if (!globalThis.SA_API_PATHS || !globalThis.SA_API_PATHS.has("/tunnel_proxy")) {
      return;
    }
    this.checkTunnelStatus();
  },

  generateQRCode() {
    if (!this.tunnelLink) return;

    const qrContainer = document.getElementById("qrcode-tunnel");
    if (!qrContainer) return;

    // Clear any existing QR code
    qrContainer.innerHTML = "";

    try {
      // Generate new QR code
      this.qrCodeInstance = new QRCode(qrContainer, {
        text: this.tunnelLink,
        width: 128,
        height: 128,
        colorDark: "#000000",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.M,
      });
    } catch (error) {
      console.error("Error generating QR code:", error);
      qrContainer.innerHTML =
        `<div class="qr-error">${t('tunnel.qrError', 'QR code generation failed')}</div>`;
    }
  },

  async checkTunnelStatus() {
    try {
      const response = await fetchApi("/tunnel_proxy", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action: "get" }),
      });

      const data = await response.json();

      if (data.success && data.tunnel_url) {
        // Update the stored URL if it's different from what we have
        if (this.tunnelLink !== data.tunnel_url) {
          this.tunnelLink = data.tunnel_url;
          localStorage.setItem("agent_zero_tunnel_url", data.tunnel_url);
        }
        this.linkGenerated = true;
        // Generate QR code for the tunnel URL
        Sleep.Skip().then(() => this.generateQRCode());
      } else {
        // Check if we have a stored tunnel URL
        const storedTunnelUrl = localStorage.getItem("agent_zero_tunnel_url");

        if (storedTunnelUrl) {
          // Use the stored URL but verify it's still valid
          const verifyResponse = await fetchApi("/tunnel_proxy", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ action: "verify", url: storedTunnelUrl }),
          });

          const verifyData = await verifyResponse.json();

          if (verifyData.success && verifyData.is_valid) {
            this.tunnelLink = storedTunnelUrl;
            this.linkGenerated = true;
            // Generate QR code for the tunnel URL
            Sleep.Skip().then(() => this.generateQRCode());
          } else {
            // Clear stale URL
            localStorage.removeItem("agent_zero_tunnel_url");
            this.tunnelLink = "";
            this.linkGenerated = false;
          }
        } else {
          // No stored URL, show the generate button
          this.tunnelLink = "";
          this.linkGenerated = false;
        }
      }
    } catch (error) {
      console.error("Error checking tunnel status:", error);
      this.tunnelLink = "";
      this.linkGenerated = false;
    }
  },

  async refreshLink() {
    // Call generate but with a confirmation first
    if (
      confirm(
        t('tunnel.refreshConfirm', 'Are you sure you want to generate a new tunnel URL? The old URL will no longer work.')
      )
    ) {

      this.isLoading = true;
      this.loadingText = t('tunnel.refreshing', 'Refreshing tunnel...');

      // Change refresh button appearance
      const refreshButton = document.querySelector("#tunnel-settings-section .refresh-link-button");
      const originalContent = refreshButton.innerHTML;
      refreshButton.innerHTML =
        `<span class="icon material-symbols-outlined spin">progress_activity</span> ${t('tunnel.refreshingShort', 'Refreshing...')}`;
      refreshButton.disabled = true;
      refreshButton.classList.add("refreshing");

      try {
        // First stop any existing tunnel
        const stopResponse = await fetchApi("/tunnel_proxy", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ action: "stop" }),
        });

        // Check if stopping was successful
        const stopData = await stopResponse.json();
        if (!stopData.success) {
          console.warn("Warning: Couldn't stop existing tunnel cleanly");
          // Continue anyway since we want to create a new one
        }

        // Then generate a new one
        await this.generateLink();
      } catch (error) {
        console.error("Error refreshing tunnel:", error);
        window.toastFrontendError(t('tunnel.refreshError', 'Error refreshing tunnel'), t('tunnel.errorTitle', 'Tunnel Error'));
        this.isLoading = false;
        this.loadingText = "";
      } finally {
        // Reset refresh button
        refreshButton.innerHTML = originalContent;
        refreshButton.disabled = false;
        refreshButton.classList.remove("refreshing");
      }
    }
  },

  async generateLink() {
    // First check if authentication is enabled
    try {
      const authCheckResponse = await fetchApi("/v1/ui/settings/sections");
      const authDataRaw = await authCheckResponse.json();
      const authData = { settings: { sections: authDataRaw.sections || [] } };

      // Find the auth_login and auth_password in the settings
      let hasAuth = false;

      if (authData && authData.settings && authData.settings.sections) {
        for (const section of authData.settings.sections) {
          if (section.fields) {
            const authLoginField = section.fields.find(
              (field) => field.id === "auth_login"
            );
            const authPasswordField = section.fields.find(
              (field) => field.id === "auth_password"
            );

            if (
              authLoginField &&
              authPasswordField &&
              authLoginField.value &&
              authPasswordField.value
            ) {
              hasAuth = true;
              break;
            }
          }
        }
      }

      // If no authentication is set, warn the user
      if (!hasAuth) {
        const proceed = confirm(
          t('tunnel.noAuthWarning', "WARNING: No authentication is configured for your Agent Zero instance.\n\nCreating a public tunnel without authentication means anyone with the URL can access your Agent Zero instance.\n\nIt is recommended to set up authentication in the Settings > Authentication section before creating a public tunnel.\n\nDo you want to proceed anyway?")
        );

        if (!proceed) {
          return; // User cancelled
        }
      }
    } catch (error) {
      console.error("Error checking authentication status:", error);
      // Continue anyway if we can't check auth status
    }

    this.isLoading = true;
    this.loadingText = t('tunnel.creating', 'Creating tunnel...');

    // Change create button appearance
    const createButton = document.querySelector("#tunnel-settings-section .tunnel-actions .btn-ok");
    if (createButton) {
      createButton.innerHTML =
        `<span class="icon material-symbols-outlined spin">progress_activity</span> ${t('tunnel.creatingShort', 'Creating...')}`;
      createButton.disabled = true;
      createButton.classList.add("creating");
    }

    try {
      // Call the backend API to create a tunnel
      const response = await fetchApi("/tunnel_proxy", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          action: "create",
          provider: this.provider,
          // port: window.location.port || (window.location.protocol === 'https:' ? 443 : 80)
        }),
      });

      const data = await response.json();

      if (data.success && data.tunnel_url) {
        // Store the tunnel URL in localStorage for persistence
        localStorage.setItem("agent_zero_tunnel_url", data.tunnel_url);

        this.tunnelLink = data.tunnel_url;
        this.linkGenerated = true;

        // Generate QR code for the tunnel URL
        Sleep.Skip().then(() => this.generateQRCode());

        // Show success message to confirm creation
        window.toastFrontendInfo(
          t('tunnel.createdSuccess', 'Tunnel created successfully'),
          t('tunnel.statusTitle', 'Tunnel Status')
        );
      } else {
        // The tunnel might still be starting up, check again after a delay
        this.loadingText = t('tunnel.slowCreate', 'Tunnel creation taking longer than expected...');

        // Wait for 5 seconds and check if the tunnel is running
        await new Promise((resolve) => setTimeout(resolve, 5000));

        // Check if tunnel is running now
        try {
          const statusResponse = await fetchApi("/tunnel_proxy", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ action: "get" }),
          });

          const statusData = await statusResponse.json();

          if (statusData.success && statusData.tunnel_url) {
            // Tunnel is now running, we can update the UI
            localStorage.setItem(
              "agent_zero_tunnel_url",
              statusData.tunnel_url
            );
            this.tunnelLink = statusData.tunnel_url;
            this.linkGenerated = true;

            // Generate QR code for the tunnel URL
            Sleep.Skip().then(() => this.generateQRCode());

            window.toastFrontendInfo(
              t('tunnel.createdSuccess', 'Tunnel created successfully'),
              t('tunnel.statusTitle', 'Tunnel Status')
            );
            return;
          }
        } catch (statusError) {
          console.error("Error checking tunnel status:", statusError);
        }

        // If we get here, the tunnel really failed to start
        const errorMessage =
          data.message || t('tunnel.createFailed', 'Failed to create tunnel. Please try again.');
        window.toastFrontendError(errorMessage, t('tunnel.errorTitle', 'Tunnel Error'));
        console.error("Tunnel creation failed:", data);
      }
    } catch (error) {
      window.toastFrontendError(t('tunnel.createError', 'Error creating tunnel'), t('tunnel.errorTitle', 'Tunnel Error'));
      console.error("Error creating tunnel:", error);
    } finally {
      this.isLoading = false;
      this.loadingText = "";

      // Reset create button if it's still in the DOM
      const createButton = document.querySelector("#tunnel-settings-section .tunnel-actions .btn-ok");
      if (createButton) {
        createButton.innerHTML =
          `<span class="icon material-symbols-outlined">play_circle</span> ${t('tunnel.create', 'Create Tunnel')}`;
        createButton.disabled = false;
        createButton.classList.remove("creating");
      }
    }
  },

  async stopTunnel() {
    if (
      confirm(
        t('tunnel.stopConfirm', 'Are you sure you want to stop the tunnel? The URL will no longer be accessible.')
      )
    ) {
      this.isLoading = true;
      this.loadingText = t('tunnel.stopping', 'Stopping tunnel...');

      const stopButton = document.querySelector("#tunnel-settings-section .stop-tunnel-container button");
      const originalStopContent = stopButton ? stopButton.innerHTML : null;
      if (stopButton) {
        stopButton.innerHTML = `<span class="icon material-symbols-outlined spin">progress_activity</span> ${t('tunnel.stoppingShort', 'Stopping...')}`;
        stopButton.disabled = true;
        stopButton.classList.add("stopping");
      }

      try {
        // Call the backend to stop the tunnel
        const response = await fetchApi("/tunnel_proxy", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ action: "stop" }),
        });

        const data = await response.json();

        if (data.success) {
          // Clear the stored URL
          localStorage.removeItem("agent_zero_tunnel_url");

          // Clear QR code
          const qrContainer = document.getElementById("qrcode-tunnel");
          if (qrContainer) {
            qrContainer.innerHTML = "";
          }
          this.qrCodeInstance = null;

          // Update UI state
          this.tunnelLink = "";
          this.linkGenerated = false;

          const t = (k, fb) => (globalThis.i18n ? i18n.t(k) : fb || k);
          window.toastFrontendInfo(
            t('tunnel.stopSuccess', 'Tunnel stopped successfully'),
            t('tunnel.statusTitle', 'Tunnel Status')
          );
        } else {
          window.toastFrontendError(t('tunnel.stopFailed', 'Failed to stop tunnel'), t('tunnel.errorTitle', 'Tunnel Error'));

          // Reset stop button
          if (stopButton && originalStopContent !== null) {
            stopButton.innerHTML = originalStopContent;
            stopButton.disabled = false;
            stopButton.classList.remove("stopping");
          }
        }
      } catch (error) {
        window.toastFrontendError(t('tunnel.stopError', 'Error stopping tunnel'), t('tunnel.errorTitle', 'Tunnel Error'));
        console.error("Error stopping tunnel:", error);

        // Reset stop button
        if (stopButton && originalStopContent !== null) {
          stopButton.innerHTML = originalStopContent;
          stopButton.disabled = false;
          stopButton.classList.remove("stopping");
        }
      } finally {
        this.isLoading = false;
        this.loadingText = "";
      }
    }
  },

  copyToClipboard() {
    if (!this.tunnelLink) return;

    const copyButton = document.querySelector("#tunnel-settings-section .copy-link-button");
    const originalContent = copyButton.innerHTML;

    navigator.clipboard
      .writeText(this.tunnelLink)
      .then(() => {
        // Update button to show success state
        copyButton.innerHTML =
          `<span class="icon material-symbols-outlined">check</span> ${t('tunnel.copySuccessButton', 'Copied!')}`;
        copyButton.classList.add("copy-success");

        // Show toast notification
        const t = (k, fb) => (globalThis.i18n ? i18n.t(k) : fb || k);
        window.toastFrontendInfo(
          t('tunnel.copySuccess', 'Tunnel URL copied to clipboard!'),
          t('tunnel.clipboardTitle', 'Clipboard')
        );

        // Reset button after 2 seconds
        setTimeout(() => {
          copyButton.innerHTML = originalContent;
          copyButton.classList.remove("copy-success");
        }, 2000);
      })
      .catch((err) => {
        console.error("Failed to copy URL: ", err);
        window.toastFrontendError(
          t('tunnel.copyError', 'Failed to copy tunnel URL'),
          t('tunnel.clipboardErrorTitle', 'Clipboard Error')
        );

        // Show error state
        copyButton.innerHTML =
          `<span class="icon material-symbols-outlined">close</span> ${t('tunnel.copyFailedButton', 'Failed')}`;
        copyButton.classList.add("copy-error");

        // Reset button after 2 seconds
        setTimeout(() => {
          copyButton.innerHTML = originalContent;
          copyButton.classList.remove("copy-error");
        }, 2000);
      });
  },
};

// convert it to alpine store
const store = createStore("tunnelStore", model);

// export for use in other files
export { store };
