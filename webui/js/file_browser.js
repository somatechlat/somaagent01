const fileBrowserModalProxy = {
  isOpen: false,
  isLoading: false,
  // Track active XHRs for in-flight uploads to support cancel
  activeUploads: {},

  browser: {
    title: "File Browser",
    currentPath: "",
    entries: [],
    parentPath: "",
    sortBy: "name",
    sortDirection: "asc",
  },

  // Initialize navigation history
  history: [],

  async openModal(path) {
    const modalEl = document.getElementById("fileBrowserModal");
    const modalAD = Alpine.$data(modalEl);

    modalAD.isOpen = true;
    modalAD.isLoading = true;
    modalAD.history = []; // reset history when opening modal

    // Initialize currentPath to root if it's empty
    if (path) modalAD.browser.currentPath = path;
    else if (!modalAD.browser.currentPath)
      modalAD.browser.currentPath = "$WORK_DIR";

    await modalAD.fetchFiles(modalAD.browser.currentPath);
  },

  isArchive(filename) {
    const archiveExts = ["zip", "tar", "gz", "rar", "7z"];
    const ext = filename.split(".").pop().toLowerCase();
    return archiveExts.includes(ext);
  },

  async fetchFiles(path = "") {
    this.isLoading = true;
    try {
      const response = await fetchApi(
        `/v1/workdir/list?path=${encodeURIComponent(path)}`
      );

      if (response.ok) {
        const data = await response.json();
        this.browser.entries = data.data.entries;
        this.browser.currentPath = data.data.current_path;
        this.browser.parentPath = data.data.parent_path;
      } else {
        console.error("Error fetching files:", await response.text());
        this.browser.entries = [];
      }
    } catch (error) {
      window.toastFrontendError("Error fetching files: " + error.message, "File Browser Error");
      this.browser.entries = [];
    } finally {
      this.isLoading = false;
    }
  },

  async navigateToFolder(path) {
    // Push current path to history before navigating
    if (this.browser.currentPath !== path) {
      this.history.push(this.browser.currentPath);
    }
    await this.fetchFiles(path);
  },

  async navigateUp() {
    if (this.browser.parentPath !== "") {
      // Push current path to history before navigating up
      this.history.push(this.browser.currentPath);
      await this.fetchFiles(this.browser.parentPath);
    }
  },

  sortFiles(entries) {
    return [...entries].sort((a, b) => {
      // Folders always come first
      if (a.is_dir !== b.is_dir) {
        return a.is_dir ? -1 : 1;
      }

      const direction = this.browser.sortDirection === "asc" ? 1 : -1;
      switch (this.browser.sortBy) {
        case "name":
          return direction * a.name.localeCompare(b.name);
        case "size":
          return direction * (a.size - b.size);
        case "date":
          return direction * (new Date(a.modified) - new Date(b.modified));
        default:
          return 0;
      }
    });
  },

  toggleSort(column) {
    if (this.browser.sortBy === column) {
      this.browser.sortDirection =
        this.browser.sortDirection === "asc" ? "desc" : "asc";
    } else {
      this.browser.sortBy = column;
      this.browser.sortDirection = "asc";
    }
  },

  async deleteFile(file) {
    if (!confirm(`Are you sure you want to delete ${file.name}?`)) {
      return;
    }

    try {
      const response = await fetchApi("/v1/workdir/delete", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          path: file.path,
          currentPath: this.browser.currentPath,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        this.browser.entries = this.browser.entries.filter(
          (entry) => entry.path !== file.path
        );
        alert("File deleted successfully.");
      } else {
        alert(`Error deleting file: ${await response.text()}`);
      }
    } catch (error) {
      window.toastFrontendError("Error deleting file: " + error.message, "File Delete Error");
      alert("Error deleting file");
    }
  },

  async handleFileUpload(event) {
    try {
      const files = event.target.files;
      if (!files.length) return;

      // Client-side progress using XHR per file for better UX
      const path = this.browser.currentPath;
      for (let i = 0; i < files.length; i++) {
        const f = files[i];
        const ext = f.name.split(".").pop().toLowerCase();
        if (!["zip", "tar", "gz", "rar", "7z"].includes(ext)) {
          if (f.size > 100 * 1024 * 1024) {
            alert(`File ${f.name} exceeds the maximum allowed size of 100MB.`);
            continue;
          }
        }
        // Add a temporary entry for progress
        const tempKey = `__uploading__:${f.name}:${Date.now()}`;
        this.browser.entries = [
          { name: f.name, path: tempKey, size: f.size, modified: new Date().toISOString(), is_dir: false, type: 'unknown', uploading: true, progress: 0 },
          ...this.browser.entries,
        ];

        await new Promise((resolve, reject) => {
          try {
            const form = new FormData();
            form.append('path', path);
            form.append('files[]', f);
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/v1/workdir/upload');
            // Save xhr for cancellation
            this.activeUploads[tempKey] = xhr;
            xhr.upload.onprogress = (e) => {
              if (e.lengthComputable) {
                const pct = Math.min(100, Math.round((e.loaded * 100) / (e.total || f.size || 1)));
                // Update temp entry progress
                this.browser.entries = this.browser.entries.map((entry) => entry.path === tempKey ? { ...entry, progress: pct } : entry);
              }
            };
            xhr.onreadystatechange = async () => {
              if (xhr.readyState === 4) {
                // Cleanup stored XHR
                delete this.activeUploads[tempKey];
                if (xhr.status >= 200 && xhr.status < 300) {
                  // Refresh listing from server and drop temp entry
                  await this.fetchFiles(path);
                  resolve();
                } else {
                  // Mark as failed visually then resolve
                  this.browser.entries = this.browser.entries.map((entry) => entry.path === tempKey ? { ...entry, uploading: false, progress: 0, uploadError: true } : entry);
                  reject(new Error(xhr.responseText || `Upload failed (${xhr.status})`));
                }
              }
            };
            xhr.send(form);
          } catch (ex) {
            reject(ex);
          }
        }).catch((e) => {
          window.toastFrontendError(`Error uploading ${f.name}: ${e?.message || e}`, 'File Upload Error');
        });
      }
      // Ensure final refresh after batch
      await this.fetchFiles(path);
    } catch (error) {
      window.toastFrontendError("Error uploading files: " + error.message, "File Upload Error");
      alert("Error uploading files");
    }
  },

  cancelUpload(file) {
    try {
      const tempKey = file && file.path;
      if (!tempKey || !tempKey.startsWith("__uploading__:")) return;
      const xhr = this.activeUploads[tempKey];
      if (xhr) {
        xhr.abort();
        delete this.activeUploads[tempKey];
      }
      // Remove the temp entry from UI
      this.browser.entries = this.browser.entries.filter((e) => e.path !== tempKey);
      window.toastInfo && window.toastInfo(`Upload canceled: ${file.name}`, 'File Upload');
    } catch (e) {
      window.toastFrontendError && window.toastFrontendError("Failed to cancel upload: " + (e?.message || e), 'File Upload');
    }
  },

  downloadFile(file) {
    const link = document.createElement("a");
    link.href = `/v1/workdir/download?path=${encodeURIComponent(file.path)}`;
    link.download = file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },
  
  // Helper Functions
  formatFileSize(size) {
    if (size === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(size) / Math.log(k));
    return parseFloat((size / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  },

  formatDate(dateString) {
    const options = {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  },

  handleClose() {
    this.isOpen = false;
  },
};

// Wait for Alpine to be ready
document.addEventListener("alpine:init", () => {
  Alpine.data("fileBrowserModalProxy", () => ({
    init() {
      Object.assign(this, fileBrowserModalProxy);
      // Ensure immediate file fetch when modal opens
      this.$watch("isOpen", async (value) => {
        if (value) {
          await this.fetchFiles(this.browser.currentPath);
        }
      });
    },
  }));
});

// Keep the global assignment for backward compatibility
window.fileBrowserModalProxy = fileBrowserModalProxy;

openFileLink = async function (path) {
  try {
    // Try treating the path as a directory first
    const listResp = await fetchApi(`/v1/workdir/list?path=${encodeURIComponent(path)}`);
    if (listResp.ok) {
      const data = await listResp.json();
      const cur = (data && data.data && data.data.current_path) || path;
      fileBrowserModalProxy.openModal(cur);
      return;
    }
  } catch (e) {
    // ignore and try as file
  }
  try {
    // Fallback: treat as a file and attempt download
    const name = (path || "").split("/").filter(Boolean).pop() || "download";
    fileBrowserModalProxy.downloadFile({ path, name });
  } catch (e) {
    window.toastFrontendError("Error opening file: " + e.message, "File Open Error");
  }
};
window.openFileLink = openFileLink;
