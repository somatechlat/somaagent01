import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";

const model = {
  // State properties
  attachments: [],
  hasAttachments: false,
  dragDropOverlayVisible: false,
  // Track active per-file uploads for cancel/retry
  activeUploads: {},
  // Upload progress tracking per attachment
  // Each attachment may have: uploading:boolean, uploadedBytes:number, totalBytes:number, status:string ('uploading'|'uploaded'|'quarantined'|'error')

  // Image modal properties
  currentImageUrl: null,
  currentImageName: null,
  imageLoaded: false,
  imageError: false,
  zoomLevel: 1,

  async init() {
    await this.initialize();
  },

  // Initialize the store
  async initialize() {
    // Setup event listeners for drag and drop
    this.setupDragDropHandlers();
    // Setup paste event listener for clipboard images
    this.setupPasteHandler();
  },

  // Basic attachment management methods
  addAttachment(attachment) {
    // Validate for duplicates
    if (this.validateDuplicates(attachment)) {
      this.attachments.push(attachment);
      this.updateAttachmentState();
    }
  },

  removeAttachment(index) {
    if (index >= 0 && index < this.attachments.length) {
      this.attachments.splice(index, 1);
      this.updateAttachmentState();
    }
  },

  clearAttachments() {
    this.attachments = [];
    this.updateAttachmentState();
  },

  validateDuplicates(newAttachment) {
    // Check if attachment already exists based on name and size
    const isDuplicate = this.attachments.some(
      (existing) =>
        existing.name === newAttachment.name &&
        existing.file &&
        newAttachment.file &&
        existing.file.size === newAttachment.file.size
    );
    return !isDuplicate;
  },

  updateAttachmentState() {
    this.hasAttachments = this.attachments.length > 0;
  },

  // Drag drop overlay control methods
  showDragDropOverlay() {
    this.dragDropOverlayVisible = true;
  },

  hideDragDropOverlay() {
    this.dragDropOverlayVisible = false;
  },

  // Setup drag and drop event handlers
  setupDragDropHandlers() {
    console.log("Setting up drag and drop handlers...");
    let dragCounter = 0;

    // Prevent default drag behaviors
    ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
      document.addEventListener(
        eventName,
        (e) => {
          e.preventDefault();
          e.stopPropagation();
        },
        false
      );
    });

    // Handle drag enter
    document.addEventListener(
      "dragenter",
      (e) => {
        console.log("Drag enter detected");
        dragCounter++;
        if (dragCounter === 1) {
          console.log("Showing drag drop overlay");
          this.showDragDropOverlay();
        }
      },
      false
    );

    // Handle drag leave
    document.addEventListener(
      "dragleave",
      (e) => {
        dragCounter--;
        if (dragCounter === 0) {
          this.hideDragDropOverlay();
        }
      },
      false
    );

    // Handle drop
    document.addEventListener(
      "drop",
      (e) => {
        console.log("Drop detected with files:", e.dataTransfer.files.length);
        dragCounter = 0;
        this.hideDragDropOverlay();

        const files = e.dataTransfer.files;
        this.handleFiles(files);
      },
      false
    );
  },

  // Setup paste event handler for clipboard images
  setupPasteHandler() {
    console.log("Setting up paste handler...");
    document.addEventListener("paste", (e) => {
      console.log("Paste event detected, target:", e.target.tagName);

      const items = e.clipboardData.items;
      let imageFound = false;
      console.log("Checking clipboard items:", items.length);

      // First, check if there are any images in the clipboard
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.indexOf("image") !== -1) {
          imageFound = true;
          const blob = item.getAsFile();
          if (blob) {
            e.preventDefault(); // Prevent default paste behavior for images
            this.handleClipboardImage(blob);
            console.log("Image detected in clipboard, processing...");
          }
          break; // Only handle the first image found
        }
      }

      // If no images found and we're in an input field, let normal text paste happen
      if (
        !imageFound &&
        (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")
      ) {
        console.log(
          "No images in clipboard, allowing normal text paste in input field"
        );
        return;
      }

      // If no images found and not in input field, do nothing
      if (!imageFound) {
        console.log("No images in clipboard");
      }
    });
  },

  // Handle clipboard image pasting
  async handleClipboardImage(blob) {
    try {
      // Generate unique filename
      const guid = this.generateGUID();
      const filename = `clipboard-${guid}.png`;

      // Create file object from blob
      const file = new File([blob], filename, { type: "image/png" });

      // Create attachment object
      const attachment = {
        file: file,
        type: "image",
        name: filename,
        extension: "png",
        displayInfo: this.getAttachmentDisplayInfo(file),
      };

      // Read as data URL for preview
      const reader = new FileReader();
      reader.onload = (e) => {
        attachment.url = e.target.result;
        this.addAttachment(attachment);
      };
      reader.readAsDataURL(file);

      // Show success feedback
      console.log("Clipboard image pasted successfully:", filename);
    } catch (error) {
      console.error("Failed to handle clipboard image:", error);
    }
  },

  // Update handleFileUpload to use the attachments store
  async handleFileUpload(event) {
    const files = event.target.files;
    // Add to store for immediate UX preview
    this.handleFiles(files, { autoUpload: true });
    // Kick off background upload (golden parity: upload on selection)
    try {
      await this.uploadFiles(Array.from(files || []));
    } catch (e) {
      console.warn("Background upload failed:", e?.message || e);
      // Non-fatal; users can still send which will retry any missing files
    }
    event.target.value = ""; // clear uploader selection to fix issue where same file is ignored the second time
  },

  // File handling logic (moved from index.js)
  handleFiles(files, opts = {}) {
    console.log("handleFiles called with", files.length, "files");
    const autoUpload = !!opts.autoUpload;
    Array.from(files).forEach((file) => {
      console.log("Processing file:", file.name, file.type);
      const ext = file.name.split(".").pop().toLowerCase();
      const isImage = ["jpg", "jpeg", "png", "bmp", "gif", "webp", "svg"].includes(
        ext
      );

      const attachment = {
        file: file,
        type: isImage ? "image" : "file",
        name: file.name,
        extension: ext,
        path: null, // will be set after successful server upload
        uploading: autoUpload,
        uploadedBytes: 0,
        totalBytes: typeof file.size === "number" ? file.size : undefined,
        status: autoUpload ? "uploading" : undefined,
        displayInfo: this.getAttachmentDisplayInfo(file),
      };

      if (isImage) {
        // Read image as data URL for preview
        const reader = new FileReader();
        reader.onload = (e) => {
          attachment.url = e.target.result;
          this.addAttachment(attachment);
        };
        reader.readAsDataURL(file);
      } else {
        // For non-image files, add directly
        this.addAttachment(attachment);
      }
      // Optionally enqueue upload
      if (autoUpload) {
        // Best-effort background upload for this file only
        this.uploadFiles([file]).catch((e) => console.warn("Auto-upload failed:", e?.message || e));
      }
    });
  },

  // Upload provided files to the server, per file, enabling cancel/retry
  async uploadFiles(filesArray) {
    const files = Array.isArray(filesArray) ? filesArray : [];
    if (!files.length) return;
    for (const f of files) {
      // Skip if we already have a server path
      const idx = this.attachments.findIndex((a) => a && a.file === f && !a.path);
      if (idx === -1) continue;
      await this._uploadSingleByIndex(idx).catch((e) => {
        console.warn("upload single failed:", e?.message || e);
      });
    }
  },

  async _uploadSingleByIndex(idx) {
    const att = this.attachments[idx];
    if (!att || !att.file) return;
    // Set uploading state
    this.attachments[idx] = { ...att, uploading: true, status: "uploading", uploadError: false };
    const form = new FormData();
    form.append("files", att.file);
    // Support cancel with AbortController via fetchApi
    const controller = new AbortController();
    this.activeUploads[att.name] = controller;
    try {
      const resp = await fetchApi("/uploads", { method: "POST", body: form, signal: controller.signal });
      if (!resp.ok) {
        const txt = await resp.text().catch(() => "");
        throw new Error(txt || `HTTP ${resp.status}`);
      }
      const arr = await resp.json();
      const first = Array.isArray(arr) ? arr.find((d) => (d.filename || d.name) === att.name) || arr[0] : null;
      const serverPath = first && typeof first.path === "string" ? first.path : null;
      const status = first && first.status;
      const attId = first && first.id;
      this.attachments[idx] = {
        ...this.attachments[idx],
        uploading: false,
        status: status || "uploaded",
        path: serverPath || this.attachments[idx].path,
        uploadedBytes: this.attachments[idx].totalBytes || this.attachments[idx].uploadedBytes || (att.file ? att.file.size : 0),
        totalBytes: this.attachments[idx].totalBytes || (att.file ? att.file.size : undefined),
        attachment_id: attId || this.attachments[idx].attachment_id,
        uploadError: false,
      };
    } catch (e) {
      // Abort is not an error UX
      const aborted = e && (e.name === "AbortError" || /abort/i.test(e.message || ""));
      this.attachments[idx] = {
        ...this.attachments[idx],
        uploading: false,
        uploadError: !aborted,
        status: aborted ? this.attachments[idx].status : "error",
      };
      if (!aborted) console.warn("Upload failed:", e?.message || e);
    } finally {
      delete this.activeUploads[att.name];
      this.updateAttachmentState();
    }
  },

  cancelAttachment(index) {
    const att = this.attachments[index];
    if (!att) return;
    const ctl = this.activeUploads[att.name];
    if (ctl) ctl.abort();
    // UI state is set in _uploadSingleByIndex catch
  },

  retryAttachment(index) {
    const att = this.attachments[index];
    if (!att || !att.file) {
      (window.toastFrontendInfo || window.toastInfo || console.info)("Please reselect the file to retry.", "Attachments");
      return;
    }
    // Reset error and kick upload
    this.attachments[index] = { ...att, uploadError: false, status: "uploading", uploading: true };
    return this._uploadSingleByIndex(index);
  },

  // Get attachments for sending message (preserve server path when available)
  getAttachmentsForSending() {
    return this.attachments.map((attachment) => {
      if (attachment.type === "image") {
        return {
          ...attachment,
          url: attachment.url || (attachment.file ? URL.createObjectURL(attachment.file) : null),
        };
      }
      return { ...attachment };
    });
  },

  // Update progress based on SSE event metadata
  // meta: { filename, bytes_uploaded, bytes_total?, status, attachment_id?, file_index? }
  updateUploadProgress(meta) {
    try {
      if (!meta) return;
      const fname = meta.filename || meta.name;
      const uploaded = typeof meta.bytes_uploaded === "number" ? meta.bytes_uploaded : 0;
      const total = typeof meta.bytes_total === "number" ? meta.bytes_total : undefined;
      const status = meta.status || (total && uploaded >= total ? "uploaded" : "uploading");
      // Find the first matching attachment without a finalized path or still uploading
      const idx = this.attachments.findIndex((a) => a && a.name === fname && (!a.path || a.uploading));
      if (idx < 0) return;
      const prev = this.attachments[idx] || {};
      const next = {
        ...prev,
        uploading: status !== "uploaded",
        status: status || prev.status,
        uploadedBytes: Math.max(prev.uploadedBytes || 0, uploaded || 0),
        totalBytes: prev.totalBytes || total || (prev.file ? prev.file.size : undefined),
        path: prev.path || (meta.attachment_id ? `/v1/attachments/${meta.attachment_id}` : prev.path),
        attachment_id: prev.attachment_id || meta.attachment_id || prev.attachment_id,
      };
      this.attachments[idx] = next;
      // Notify user if AV quarantined the file
      if (next.status === 'quarantined' && prev.status !== 'quarantined') {
        (window.toastFrontendWarning || window.toastWarning || console.warn)(`Attachment quarantined by antivirus: ${fname}`, 'Attachments');
      }
      this.updateAttachmentState();
    } catch (e) {
      console.warn("updateUploadProgress error:", e?.message || e);
    }
  },

  // Convenience: return only already-uploaded server paths
  getServerAttachmentPaths() {
    return this.attachments
      .map((a) => a && a.path)
      .filter((p) => typeof p === "string" && p.length > 0);
  },

  // Generate server-side API URL for file (for device sync)
  getServerImgUrl(filename) {
    // Prefer /v1/attachments path when available (set on server-returned objects)
    // For filename-only references (legacy), we don't know the absolute path on disk safely.
    // Fall back to a generic file icon; preview for server-stored attachments handled below.
    return null;
  },

  getServerFileUrl(filename) {
    // Unknown absolute path for legacy filename-only; disable direct server URL
    return null;
  },

  // Check if file is an image based on extension
  isImageFile(filename) {
    const imageExtensions = ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"];
    const extension = filename.split(".").pop().toLowerCase();
    return imageExtensions.includes(extension);
  },

  // Get attachment preview URL (server URL for persistence, blob URL for current session)
  getAttachmentPreviewUrl(attachment) {
    // If attachment has a name and we're dealing with a server-stored file
    if (typeof attachment === "string") {
      // attachment is just a filename (from loaded chat)
      return null;
    } else if (attachment.name && attachment.file) {
      // attachment is an object from current session
      if (attachment.type === "image") {
        // For images, use blob URL for current session preview
        return attachment.url || URL.createObjectURL(attachment.file);
      } else {
        // Non-image: use static icon
        return this.getFilePreviewUrl(attachment.name);
      }
    }
    return null;
  },

  getFilePreviewUrl(filename) {
    const extension = filename.split(".").pop().toLowerCase();
    const types = {
      // Archive files
      zip: "archive",
      rar: "archive",
      "7z": "archive",
      tar: "archive",
      gz: "archive",
      // Document files
      pdf: "document",
      doc: "document",
      docx: "document",
      txt: "document",
      rtf: "document",
      odt: "document",
      // Code files
      py: "code",
      js: "code",
      html: "code",
      css: "code",
      json: "code",
      xml: "code",
      md: "code",
      yml: "code",
      yaml: "code",
      sql: "code",
      sh: "code",
      bat: "code",
      // Spreadsheet files
      xls: "document",
      xlsx: "document",
      csv: "document",
      // Presentation files
      ppt: "document",
      pptx: "document",
      odp: "document",
    };
    const type = types[extension] || "file";
    return `/public/${type}.svg`;
  },

  // Enhanced method to get attachment display info for UI
  getAttachmentDisplayInfo(attachment) {
    if (typeof attachment === "string") {
      // attachment is filename only (from persistent storage)
      const filename = attachment;
      const extension = filename.split(".").pop();
      const isImage = this.isImageFile(filename);
      const previewUrl = this.getFilePreviewUrl(filename);

      return {
        filename: filename,
        extension: extension.toUpperCase(),
        isImage: isImage,
        previewUrl: previewUrl,
        clickHandler: () => {
          window.toastFrontendWarning("Server preview for this file isn't available in this build.", "Attachments");
        },
      };
    } else {
      // attachment is object (from current session)
      const isImage = this.isImageFile(attachment.name) || (attachment.mime && attachment.mime.startsWith("image/"));
      const filename = attachment.name;
      const extension = filename.split(".").pop() || "";
      // Prefer server-provided attachment path (Gateway /v1/attachments/{id})
      const serverPath = typeof attachment.path === "string" && attachment.path.startsWith("/v1/attachments/")
        ? attachment.path
        : null;
      const previewUrl = isImage
        ? (attachment.url || serverPath || null)
        : this.getFilePreviewUrl(attachment.name);
      return {
        filename: filename,
        extension: extension.toUpperCase(),
        isImage: isImage,
        previewUrl: previewUrl,
        clickHandler: () => {
          if (isImage) {
            const imageUrl = previewUrl || serverPath;
            if (imageUrl) this.openImageModal(imageUrl, attachment.name);
            else window.toastFrontendWarning("Preview not available for this attachment.", "Attachments");
          } else {
            if (serverPath) {
              // Trigger download via hyperlink for attachments endpoint
              const link = document.createElement("a");
              link.href = serverPath;
              link.download = filename;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
            } else {
              window.toastFrontendWarning("Download not available for this file.", "Attachments");
            }
          }
        },
      };
    }
  },

  async downloadAttachment(filename) {
    try {
      const path = this.getServerFileUrl(filename);
      if (!path) throw new Error("No server path available for this file");
      const response = await fetchApi("/v1/workdir/download?path=" + encodeURIComponent(path));

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const blob = await response.blob();

      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(link.href);
    } catch (error) {
      window.toastFetchError("Error downloading file", error);
      alert("Error downloading file");
    }
  },

  // Generate GUID for unique filenames
  generateGUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
      /[xy]/g,
      function (c) {
        const r = (Math.random() * 16) | 0;
        const v = c == "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      }
    );
  },

  // Image modal methods
  openImageModal(imageUrl, imageName) {
    this.currentImageUrl = imageUrl;
    this.currentImageName = imageName;
    this.imageLoaded = false;
    this.imageError = false;
    this.zoomLevel = 1;

    // Open the modal using the modals system
    if (window.openModal) {
      window.openModal("chat/attachments/imageModal.html");
    }
  },

  closeImageModal() {
    this.currentImageUrl = null;
    this.currentImageName = null;
    this.imageLoaded = false;
    this.imageError = false;
    this.zoomLevel = 1;
  },

  // Zoom controls
  zoomIn() {
    this.zoomLevel = Math.min(this.zoomLevel * 1.2, 5); // Max 5x zoom
    this.updateImageZoom();
  },

  zoomOut() {
    this.zoomLevel = Math.max(this.zoomLevel / 1.2, 0.1); // Min 0.1x zoom
    this.updateImageZoom();
  },

  resetZoom() {
    this.zoomLevel = 1;
    this.updateImageZoom();
  },

  updateImageZoom() {
    const img = document.querySelector(".modal-image");
    if (img) {
      img.style.transform = `scale(${this.zoomLevel})`;
    }
  },
};

const store = createStore("chatAttachments", model);

export { store };
