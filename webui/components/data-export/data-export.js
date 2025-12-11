/**
 * Data Export Component
 * Export to JSON, Markdown, PDF
 * Requirements: 25.1, 25.2, 25.3, 25.4, 25.5
 */

/**
 * Data Export Utility
 */
export class DataExporter {
  /**
   * Export data to JSON file
   * @param {Object} data - Data to export
   * @param {string} filename - Output filename
   */
  static exportJSON(data, filename = 'export.json') {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    this.downloadBlob(blob, filename);
  }

  /**
   * Export chat session to Markdown
   * @param {Object} session - Session data with messages
   * @param {string} filename - Output filename
   */
  static exportMarkdown(session, filename = 'chat.md') {
    let markdown = `# ${session.name || 'Chat Session'}\n\n`;
    markdown += `**Date:** ${new Date(session.created_at || Date.now()).toLocaleString()}\n\n`;
    markdown += `---\n\n`;

    if (session.messages && session.messages.length > 0) {
      for (const msg of session.messages) {
        const role = msg.role === 'user' ? '**You**' : '**Agent**';
        const time = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : '';
        
        markdown += `### ${role} ${time ? `(${time})` : ''}\n\n`;
        markdown += `${msg.content}\n\n`;
        
        // Include tool calls if present
        if (msg.tools && msg.tools.length > 0) {
          markdown += `<details>\n<summary>Tool Calls</summary>\n\n`;
          for (const tool of msg.tools) {
            markdown += `- **${tool.name}**: ${tool.status}\n`;
            if (tool.output) {
              markdown += `  \`\`\`\n  ${JSON.stringify(tool.output, null, 2)}\n  \`\`\`\n`;
            }
          }
          markdown += `</details>\n\n`;
        }
        
        markdown += `---\n\n`;
      }
    }

    const blob = new Blob([markdown], { type: 'text/markdown' });
    this.downloadBlob(blob, filename);
  }

  /**
   * Export memories to Markdown
   * @param {Array} memories - Array of memory objects
   * @param {string} filename - Output filename
   */
  static exportMemoriesMarkdown(memories, filename = 'memories.md') {
    let markdown = `# Agent Memories\n\n`;
    markdown += `**Exported:** ${new Date().toLocaleString()}\n`;
    markdown += `**Total:** ${memories.length} memories\n\n`;
    markdown += `---\n\n`;

    for (const mem of memories) {
      markdown += `## ${mem.type || 'Memory'}\n\n`;
      markdown += `**Score:** ${mem.score ? (mem.score * 100).toFixed(1) + '%' : 'N/A'}\n`;
      markdown += `**Date:** ${mem.timestamp ? new Date(mem.timestamp).toLocaleString() : 'Unknown'}\n\n`;
      markdown += `${mem.content}\n\n`;
      markdown += `---\n\n`;
    }

    const blob = new Blob([markdown], { type: 'text/markdown' });
    this.downloadBlob(blob, filename);
  }

  /**
   * Export to PDF (using browser print)
   * @param {string} content - HTML content to print
   * @param {string} title - Document title
   */
  static exportPDF(content, title = 'Export') {
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      alert('Please allow popups to export PDF');
      return;
    }

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>${title}</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            color: #333;
          }
          h1, h2, h3 { margin-top: 1.5em; }
          pre {
            background: #f5f5f5;
            padding: 1em;
            border-radius: 4px;
            overflow-x: auto;
          }
          code {
            font-family: 'Fira Code', monospace;
            font-size: 0.9em;
          }
          .message {
            margin: 1em 0;
            padding: 1em;
            border-left: 3px solid #ddd;
          }
          .message.user { border-color: #4f46e5; }
          .message.assistant { border-color: #10b981; }
          @media print {
            body { padding: 20px; }
          }
        </style>
      </head>
      <body>
        ${content}
      </body>
      </html>
    `);

    printWindow.document.close();
    printWindow.focus();
    
    // Wait for content to load then print
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 500);
  }

  /**
   * Export chat session to PDF
   * @param {Object} session - Session data with messages
   */
  static exportSessionPDF(session) {
    let html = `<h1>${session.name || 'Chat Session'}</h1>`;
    html += `<p><strong>Date:</strong> ${new Date(session.created_at || Date.now()).toLocaleString()}</p>`;
    html += `<hr>`;

    if (session.messages && session.messages.length > 0) {
      for (const msg of session.messages) {
        const role = msg.role === 'user' ? 'You' : 'Agent';
        const roleClass = msg.role === 'user' ? 'user' : 'assistant';
        
        html += `<div class="message ${roleClass}">`;
        html += `<strong>${role}</strong>`;
        html += `<div>${this.escapeHtml(msg.content).replace(/\n/g, '<br>')}</div>`;
        html += `</div>`;
      }
    }

    this.exportPDF(html, session.name || 'Chat Export');
  }

  /**
   * Export all sessions to JSON
   * @param {Array} sessions - Array of session objects
   */
  static exportAllSessions(sessions) {
    const data = {
      exported_at: new Date().toISOString(),
      total_sessions: sessions.length,
      sessions: sessions
    };
    this.exportJSON(data, `sessions_${Date.now()}.json`);
  }

  /**
   * Export all memories to JSON
   * @param {Array} memories - Array of memory objects
   */
  static exportAllMemories(memories) {
    const data = {
      exported_at: new Date().toISOString(),
      total_memories: memories.length,
      memories: memories
    };
    this.exportJSON(data, `memories_${Date.now()}.json`);
  }

  /**
   * Download blob as file
   * @param {Blob} blob - Blob to download
   * @param {string} filename - Output filename
   */
  static downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * Escape HTML special characters
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  static escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

/**
 * Data Export Alpine Component
 */
export function createDataExport() {
  return {
    // State
    isOpen: false,
    exportType: 'session',
    format: 'json',
    isExporting: false,
    
    // Options
    exportTypes: [
      { id: 'session', label: 'Current Session', icon: 'chat' },
      { id: 'all-sessions', label: 'All Sessions', icon: 'folder' },
      { id: 'memories', label: 'Memories', icon: 'psychology' },
      { id: 'settings', label: 'Settings', icon: 'settings' }
    ],
    
    formats: [
      { id: 'json', label: 'JSON', icon: 'code' },
      { id: 'markdown', label: 'Markdown', icon: 'description' },
      { id: 'pdf', label: 'PDF', icon: 'picture_as_pdf' }
    ],
    
    // Methods
    open() {
      this.isOpen = true;
    },
    
    close() {
      this.isOpen = false;
    },
    
    async doExport() {
      this.isExporting = true;
      
      try {
        switch (this.exportType) {
          case 'session':
            await this.exportCurrentSession();
            break;
          case 'all-sessions':
            await this.exportAllSessions();
            break;
          case 'memories':
            await this.exportMemories();
            break;
          case 'settings':
            await this.exportSettings();
            break;
        }
        
        this.$dispatch('toast', { type: 'success', message: 'Export completed!' });
        this.close();
      } catch (err) {
        console.error('Export failed:', err);
        this.$dispatch('toast', { type: 'error', message: 'Export failed: ' + err.message });
      } finally {
        this.isExporting = false;
      }
    },
    
    async exportCurrentSession() {
      // Get current session from store
      const session = Alpine.store('chat')?.currentSession || {};
      const messages = Alpine.store('chat')?.messages || [];
      const data = { ...session, messages };
      
      switch (this.format) {
        case 'json':
          DataExporter.exportJSON(data, `session_${session.id || 'export'}.json`);
          break;
        case 'markdown':
          DataExporter.exportMarkdown(data, `session_${session.id || 'export'}.md`);
          break;
        case 'pdf':
          DataExporter.exportSessionPDF(data);
          break;
      }
    },
    
    async exportAllSessions() {
      const sessions = Alpine.store('sessions')?.sessions || [];
      
      if (this.format === 'json') {
        DataExporter.exportAllSessions(sessions);
      } else {
        // For markdown/pdf, export each session
        for (const session of sessions) {
          if (this.format === 'markdown') {
            DataExporter.exportMarkdown(session, `session_${session.id}.md`);
          }
        }
      }
    },
    
    async exportMemories() {
      const memories = Alpine.store('memory')?.memories || [];
      
      switch (this.format) {
        case 'json':
          DataExporter.exportAllMemories(memories);
          break;
        case 'markdown':
          DataExporter.exportMemoriesMarkdown(memories);
          break;
        case 'pdf':
          // Convert to HTML and export
          let html = '<h1>Agent Memories</h1>';
          for (const mem of memories) {
            html += `<div class="message"><strong>${mem.type}</strong><p>${DataExporter.escapeHtml(mem.content)}</p></div>`;
          }
          DataExporter.exportPDF(html, 'Memories Export');
          break;
      }
    },
    
    async exportSettings() {
      const settings = Alpine.store('settings')?.sections || [];
      DataExporter.exportJSON({ settings }, 'settings_backup.json');
    }
  };
}

/**
 * Register Alpine component
 */
export function registerDataExport() {
  if (typeof Alpine !== 'undefined') {
    Alpine.data('dataExport', createDataExport);
  }
}

export { DataExporter };
export default createDataExport;
