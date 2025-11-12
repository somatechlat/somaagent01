import { createStore } from "/js/AlpineStore.js";
import { fetchApi } from "/js/api.js";
import { uploadFileChunked } from "/js/uploadsChunked.js";

const model = {
  // State properties
  attachments: [], // working list (pre-upload and uploaded descriptors)
  hasAttachments: false,
  dragDropOverlayVisible: false,
  uploading: false,
  sessionId: null,

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
    if (this.validateDuplicates(attachment)) {
      // initialize upload tracking fields (will be populated once upload starts)
      attachment.progressBytes = 0;
      attachment.totalBytes = attachment.file ? attachment.file.size : 0;
      attachment.status = "pending"; // pending | uploading | uploaded | error | quarantined
      attachment.attachmentId = null;
      attachment.sha256 = null;
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
  handleFileUpload(event) {
    const files = event.target.files;
    this.handleFiles(files);
    event.target.value = ""; // clear uploader selection to fix issue where same file is ignored the second time
  },

  // File handling logic (moved from index.js)
  handleFiles(files) {
    console.log("handleFiles called with", files.length, "files");
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
    });
  },

  // Get attachments for sending message
  getAttachmentsForSending() {
    // Return list of successfully uploaded descriptor objects for message send
    return this.attachments
      .filter((a) => a.status === "uploaded" || a.status === "quarantined")
      .map((a) => ({
        id: a.attachmentId,
        filename: a.name,
        mime: a.file?.type || "application/octet-stream",
        size: a.totalBytes,
        sha256: a.sha256,
        status: a.status,
         path: a.path || null, // set after upload
      }));
  },

  // Generate server-side API URL for file (for device sync)
   // Prior server URLs removed; use attachment descriptors with .path

  // Check if file is an image based on extension
  isImageFile(filename) {
    const imageExtensions = ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"];
    const extension = filename.split(".").pop().toLowerCase();
    return imageExtensions.includes(extension);
  },

  // Get attachment preview URL (server URL for persistence, blob URL for current session)
  getAttachmentPreviewUrl(attachment) {
    if (!attachment) return null;
    // uploaded descriptor (has path)
    if (attachment.path) {
      return attachment.mime && attachment.mime.startsWith("image/") ? attachment.path : this.getFilePreviewUrl(attachment.filename || attachment.name);
    }
    // pre-upload object with file
    if (attachment.file) {
      if (attachment.type === "image") return attachment.url || URL.createObjectURL(attachment.file);
      return this.getFilePreviewUrl(attachment.name);
    }
    if (typeof attachment === "string") return this.getServerImgUrl(attachment);
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
    // If descriptor returned from backend
    if (attachment && attachment.attachmentId && attachment.path) {
      const isImage = attachment.mime && attachment.mime.startsWith("image/");
      return {
        filename: attachment.filename || attachment.name,
        extension: (attachment.filename || attachment.name || "").split(".").pop().toUpperCase(),
        isImage,
        previewUrl: isImage ? attachment.path : this.getFilePreviewUrl(attachment.filename || attachment.name),
        clickHandler: () => {
          if (isImage) {
            this.openImageModal(attachment.path, attachment.filename || attachment.name);
          } else {
            window.open(attachment.path, "_blank");
          }
        },
        progressBytes: attachment.progressBytes,
        totalBytes: attachment.totalBytes,
        status: attachment.status,
      };
    }
    // Pre-upload object
    if (attachment && attachment.file) {
      const isImage = attachment.type === "image";
      return {
        filename: attachment.name,
        extension: (attachment.name || "").split(".").pop().toUpperCase(),
        isImage,
        previewUrl: this.getAttachmentPreviewUrl(attachment),
        clickHandler: () => {
          if (isImage && attachment.url) {
            this.openImageModal(attachment.url, attachment.name);
          }
        },
        progressBytes: attachment.progressBytes,
        totalBytes: attachment.totalBytes,
        status: attachment.status,
      };
    }
    // Fallback string filename
    if (typeof attachment === "string") {
      const isImage = this.isImageFile(attachment);
      return {
        filename: attachment,
        extension: (attachment.split(".").pop() || "").toUpperCase(),
        isImage,
        previewUrl: isImage ? this.getServerImgUrl(attachment) : this.getFilePreviewUrl(attachment),
        clickHandler: () => {
          if (isImage) this.openImageModal(this.getServerImgUrl(attachment), attachment);
        },
        progressBytes: null,
        totalBytes: null,
        status: "unknown",
      };
    }
    return {
      filename: "unknown",
      extension: "",
      isImage: false,
      previewUrl: null,
      clickHandler: () => {},
      progressBytes: null,
      totalBytes: null,
      status: "unknown",
    };
  },

  async uploadAll(sessionId) {
    if (!this.attachments.length) return [];
    this.uploading = true;
    this.sessionId = sessionId;
    const CHUNK_THRESHOLD = 8 * 1024 * 1024; // 8MB
    const pending = this.attachments.filter(a => a.status === "pending");
    try {
      const small = pending.filter(a => (a.file?.size || 0) <= CHUNK_THRESHOLD);
      const large = pending.filter(a => (a.file?.size || 0) > CHUNK_THRESHOLD);
      let results = [];
      // Upload large files via chunked API, sequentially
      for (const a of large) {
        a.status = "uploading";
        const d = await this.uploadChunked(a, sessionId);
        if (d) {
          a.status = d.status === "quarantined" ? "quarantined" : "uploaded";
          a.attachmentId = d.id;
          a.sha256 = d.sha256;
          a.path = d.path;
          a.progressBytes = a.totalBytes;
          results.push(d);
        } else {
          a.status = "error";
        }
      }
      // Upload small files in one batch
      if (small.length) {
        small.forEach(a => a.status = "uploading");
        const form = new FormData();
        form.append("session_id", sessionId || "");
        small.forEach(a => form.append("files", a.file, a.name));
        const resp = await fetch("/v1/uploads", { method: "POST", body: form, credentials: "same-origin" });
        if (!resp.ok) {
          const txt = await resp.text();
          small.forEach(a => { a.status = "error"; a.error = txt; });
        } else {
          const descriptors = await resp.json();
          descriptors.forEach(d => {
            const match = this.attachments.find(x => x.name === d.filename && (x.status === "uploading" || x.status === "pending"));
            if (match) {
              match.status = d.status === "quarantined" ? "quarantined" : "uploaded";
              match.attachmentId = d.id;
              match.sha256 = d.sha256;
              match.path = d.path;
              match.progressBytes = match.totalBytes;
            }
            results.push(d);
          });
        }
      }
      return results;
    } catch (err) {
      pending.forEach(a => { a.status = "error"; a.error = err?.message || String(err); });
      return [];
    } finally {
      this.uploading = false;
      this.updateAttachmentState();
    }
  },

  async retryAttachment(attachment) {
    if (!attachment || !attachment.file) return;
    attachment.status = 'pending';
    attachment.progressBytes = 0;
    attachment.error = null;
    // Clear resume key in case it existed
    const resumeKey = `chunk-upload:${this.sessionId||'unspecified'}:${attachment.name}:${attachment.file.size}`;
    sessionStorage.removeItem(resumeKey);
    // Decide path: chunked vs single
    const CHUNK_THRESHOLD = 8 * 1024 * 1024;
    if ((attachment.file.size||0) > CHUNK_THRESHOLD) {
      attachment.status = 'uploading';
      const d = await this.uploadChunked(attachment, this.sessionId);
      if (d) {
        attachment.status = d.status === 'quarantined' ? 'quarantined' : 'uploaded';
        attachment.attachmentId = d.id; attachment.sha256 = d.sha256; attachment.path = d.path;
        attachment.progressBytes = attachment.totalBytes;
      } else {
        attachment.status = 'error';
      }
    } else {
      // Single file POST
      const form = new FormData();
      form.append('session_id', this.sessionId || '');
      form.append('files', attachment.file, attachment.name);
      attachment.status = 'uploading';
      const resp = await fetch('/v1/uploads', { method: 'POST', body: form, credentials: 'same-origin' });
      if (resp.ok) {
        const arr = await resp.json();
        const d = arr.find(x => x.filename === attachment.name);
        if (d) {
          attachment.status = d.status === 'quarantined' ? 'quarantined' : 'uploaded';
          attachment.attachmentId = d.id; attachment.sha256 = d.sha256; attachment.path = d.path;
          attachment.progressBytes = attachment.totalBytes;
        } else {
          attachment.status = 'error';
        }
      } else {
        attachment.status = 'error';
      }
    }
    this.updateAttachmentState();
  },

  async resumeAttachment(attachment) {
    if (!attachment || !attachment.file) return;
    if (attachment.status !== 'uploading') return; // only resume mid-upload
    // Simply invoke chunked path which will detect existing offset via sessionStorage key
    const CHUNK_THRESHOLD = 8 * 1024 * 1024;
    if ((attachment.file.size||0) <= CHUNK_THRESHOLD) return; // not chunked
    const d = await this.uploadChunked(attachment, this.sessionId);
    if (d) {
      attachment.status = d.status === 'quarantined' ? 'quarantined' : 'uploaded';
      attachment.attachmentId = d.id; attachment.sha256 = d.sha256; attachment.path = d.path;
      attachment.progressBytes = attachment.totalBytes;
    }
    this.updateAttachmentState();
  },

  async uploadChunked(attachment, sessionId) {
    try {
      const descriptor = await uploadFileChunked(attachment.file, sessionId, (info) => {
        attachment.progressBytes = info.bytesUploaded;
        attachment.speedBps = info.speedBps;
        attachment.etaSeconds = info.etaSeconds;
        if (info.done) attachment.status = "uploading"; // will be flipped on finalize event
      }, { resume: true });
      return descriptor;
    } catch (e) {
      return null;
    }
  },

  // Update progress from SSE uploads.progress events
  applyProgressEvent(ev) {
    if (!ev?.metadata?.filename) return;
    const filename = ev.metadata.filename;
    const match = this.attachments.find(a => a.name === filename);
    if (!match) return;
    if (typeof ev.metadata.bytes_uploaded === "number") {
      match.progressBytes = ev.metadata.bytes_uploaded;
    }
    if (ev.metadata.status === "uploaded") {
      match.progressBytes = match.totalBytes;
      match.status = ev.metadata.status;
      if (ev.metadata.attachment_id) match.attachmentId = ev.metadata.attachment_id;
      if (typeof ev.metadata.bytes_total === "number") {
        match.bytesTotal = ev.metadata.bytes_total;
      }
    } else if (ev.metadata.status === "uploading") {
      match.status = "uploading";
    }
    // percent & speed derived
    if (typeof match.progressBytes === "number" && typeof match.totalBytes === "number" && match.totalBytes > 0) {
      match.percent = match.progressBytes / match.totalBytes;
    }
  },

  // Download an attachment (item has .path produced by backend)
  async downloadAttachment(item) {
    try {
      const url = (item && item.path) ? item.path : null;
      if (!url) {
        window.toastFetchError("Attachment not downloadable", "No path available");
        return;
      }
      const a = document.createElement("a");
      a.href = url;
      a.target = "_blank";
      a.rel = "noopener";
      a.click();
    } catch (error) {
      window.toastFetchError("Error downloading file", error);
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
