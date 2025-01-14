// copy button
import { openImageModal } from "./image_modal.js";

function createCopyButton() {
  const button = document.createElement("button");
  button.className = "copy-button";
  button.textContent = "Copy";

  button.addEventListener("click", async function (e) {
    e.stopPropagation();
    const container = this.closest(".msg-content, .kvps-row, .message-text");
    let textToCopy;

    if (container.classList.contains("kvps-row")) {
      textToCopy = container.querySelector(".kvps-val").textContent;
    } else if (container.classList.contains("message-text")) {
      textToCopy = container.querySelector("span").textContent;
    } else {
      textToCopy = container.querySelector("span").textContent;
    }

    try {
      await navigator.clipboard.writeText(textToCopy);
      const originalText = button.textContent;
      button.classList.add("copied");
      button.textContent = "Copied!";
      setTimeout(() => {
        button.classList.remove("copied");
        button.textContent = originalText;
      }, 2000);
    } catch (err) {
      console.error("Failed to copy text:", err);
    }
  });

  return button;
}

function addCopyButtonToElement(element) {
  if (!element.querySelector(".copy-button")) {
    element.appendChild(createCopyButton());
  }
}

export function getHandler(type) {
  switch (type) {
    case "user":
      return drawMessageUser;
    case "agent":
      return drawMessageAgent;
    case "response":
      return drawMessageResponse;
    case "tool":
      return drawMessageTool;
    case "code_exe":
      return drawMessageCodeExe;
    case "browser":
      return drawMessageBrowser;
    case "warning":
      return drawMessageWarning;
    case "rate_limit":
      return drawMessageWarning;
    case "error":
      return drawMessageError;
    case "info":
      return drawMessageInfo;
    case "util":
      return drawMessageUtil;
    case "hint":
      return drawMessageInfo;
    default:
      return drawMessageDefault;
  }
}

// draw a message with a specific type
export function _drawMessage(
  messageContainer,
  heading,
  content,
  temp,
  followUp,
  kvps = null,
  messageClasses = [],
  contentClasses = [],
  latex = false
) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", ...messageClasses);

  if (heading) {
    const headingElement = document.createElement("h4");
    headingElement.textContent = heading;
    messageDiv.appendChild(headingElement);
  }

  drawKvps(messageDiv, kvps, latex);

  if (content && content.trim().length > 0) {
    const preElement = document.createElement("pre");
    preElement.classList.add("msg-content", ...contentClasses);
    preElement.style.whiteSpace = "pre-wrap";
    preElement.style.wordBreak = "break-word";

    const spanElement = document.createElement("span");
    spanElement.innerHTML = escapeHTML(content);

    // Add click handler for small screens
    spanElement.addEventListener("click", () => {
      copyText(spanElement.textContent, spanElement);
    });

    preElement.appendChild(spanElement);
    addCopyButtonToElement(preElement);
    messageDiv.appendChild(preElement);

    // Render LaTeX math within the span
    if (window.renderMathInElement && latex) {
      renderMathInElement(spanElement, {
        delimiters: [
          { left: "$", right: "$", display: true }
        ],
        throwOnError: false,
      });
    }
  }

  messageContainer.appendChild(messageDiv);

  if (followUp) {
    messageContainer.classList.add("message-followup");
  }

  return messageDiv;
}

export function drawMessageDefault(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  const messageContent = convertImageTags(content); // Convert image tags
  _drawMessage(
    messageContainer,
    heading,
    messageContent,
    temp,
    false,
    kvps,
    ["message-ai", "message-default"],
    ["msg-json"]
  );
}

export function drawMessageAgent(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  let kvpsFlat = null;
  if (kvps) {
    kvpsFlat = { ...kvps, ...(kvps["tool_args"] || {}) };
    delete kvpsFlat["tool_args"];
  }

  const messageContent = convertImageTags(content); // Convert image tags
  _drawMessage(
    messageContainer,
    heading,
    messageContent,
    temp,
    false,
    kvpsFlat,
    ["message-ai", "message-agent"],
    ["msg-json"],
    true
  );
}

export function drawMessageResponse(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  const messageContent = convertImageTags(content); // Convert image tags
  _drawMessage(
    messageContainer,
    heading,
    messageContent,
    temp,
    true,
    null,
    ["message-ai", "message-agent-response"],
    [],
    true
  );
}

export function drawMessageDelegation(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  const messageContent = convertImageTags(content); // Convert image tags
  _drawMessage(
    messageContainer,
    heading,
    messageContent,
    temp,
    true,
    kvps,
    ["message-ai", "message-agent", "message-agent-delegation"],
    [],
    true
  );
}

export function drawMessageUser(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null,
  latex = true
) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", "message-user");

  const headingElement = document.createElement("h4");
  headingElement.textContent = "User message";
  messageDiv.appendChild(headingElement);

  if (content && content.trim().length > 0) {
    const textDiv = document.createElement("div");
    textDiv.classList.add("message-text");
    
    // Create a span for the content
    const spanElement = document.createElement("span");
    spanElement.textContent = content;
    textDiv.appendChild(spanElement);

    // Add click handler
    textDiv.addEventListener("click", () => {
      copyText(content, textDiv);
    });

    addCopyButtonToElement(textDiv);
    messageDiv.appendChild(textDiv);
  }

  // Handle attachments
  if (kvps && kvps.attachments && kvps.attachments.length > 0) {
    const attachmentsContainer = document.createElement("div");
    attachmentsContainer.classList.add("attachments-container");

    kvps.attachments.forEach((attachment) => {
      const attachmentDiv = document.createElement("div");
      attachmentDiv.classList.add("attachment-item");

      if (typeof attachment === "string") {
        // attachment is filename
        const filename = attachment;
        const extension = filename.split(".").pop().toUpperCase();

        attachmentDiv.classList.add("file-type");
        attachmentDiv.innerHTML = `
                    <div class="file-preview">
                        <span class="filename">${filename}</span>
                        <span class="extension">${extension}</span>
                    </div>
                `;
      } else if (attachment.type === "image") {
        // Existing logic for images
        const imgWrapper = document.createElement("div");
        imgWrapper.classList.add("image-wrapper");

        const img = document.createElement("img");
        img.src = attachment.url;
        img.alt = attachment.name;
        img.classList.add("attachment-preview");

        const fileInfo = document.createElement("div");
        fileInfo.classList.add("file-info");
        fileInfo.innerHTML = `
                    <span class="filename">${attachment.name}</span>
                    <span class="extension">${attachment.extension.toUpperCase()}</span>
                `;

        imgWrapper.appendChild(img);
        attachmentDiv.appendChild(imgWrapper);
        attachmentDiv.appendChild(fileInfo);
      } else {
        // Existing logic for non-image files
        attachmentDiv.classList.add("file-type");
        attachmentDiv.innerHTML = `
                    <div class="file-preview">
                        <span class="filename">${attachment.name}</span>
                        <span class="extension">${attachment.extension.toUpperCase()}</span>
                    </div>
                `;
      }

      attachmentsContainer.appendChild(attachmentDiv);
    });

    messageDiv.appendChild(attachmentsContainer);
  }

  messageContainer.appendChild(messageDiv);
}

export function drawMessageTool(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  const messageContent = convertImageTags(content); // Convert image tags
  _drawMessage(
    messageContainer,
    heading,
    messageContent,
    temp,
    true,
    kvps,
    ["message-ai", "message-tool"],
    ["msg-output"]
  );
}

export function drawMessageCodeExe(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  const messageContent = convertImageTags(content); // Convert image tags
  _drawMessage(messageContainer, heading, messageContent, temp, true, null, [
    "message-ai",
    "message-code-exe",
  ]);
}

export function drawMessageBrowser(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  const messageContent = convertImageTags(content); // Convert image tags
  _drawMessage(
    messageContainer,
    heading,
    messageContent,
    temp,
    true,
    kvps,
    ["message-ai", "message-browser"],
    ["msg-json"]
  );
}

export function drawMessageAgentPlain(
  classes,
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  const messageContent = convertImageTags(content); // Convert image tags
  _drawMessage(messageContainer, heading, messageContent, temp, false, kvps, [
    ...classes,
  ]);
  messageContainer.classList.add("center-container");
}

export function drawMessageInfo(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  return drawMessageAgentPlain(
    ["message-info"],
    messageContainer,
    id,
    type,
    heading,
    content,
    temp,
    kvps
  );
}

export function drawMessageUtil(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  const messageContent = convertImageTags(content); // Convert image tags
  _drawMessage(
    messageContainer,
    heading,
    messageContent,
    temp,
    false,
    kvps,
    ["message-util"],
    ["msg-json"]
  );
  messageContainer.classList.add("center-container");
}

export function drawMessageWarning(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  return drawMessageAgentPlain(
    ["message-warning"],
    messageContainer,
    id,
    type,
    heading,
    content,
    temp,
    kvps
  );
}

export function drawMessageError(
  messageContainer,
  id,
  type,
  heading,
  content,
  temp,
  kvps = null
) {
  return drawMessageAgentPlain(
    ["message-error"],
    messageContainer,
    id,
    type,
    heading,
    content,
    temp,
    kvps
  );
}

function drawKvps(container, kvps, latex) {
  if (kvps) {
    const table = document.createElement("table");
    table.classList.add("msg-kvps");
    for (let [key, value] of Object.entries(kvps)) {
      const row = table.insertRow();
      row.classList.add("kvps-row");
      if (key === "thoughts" || key === "reflection")
        row.classList.add("msg-thoughts");

      const th = row.insertCell();
      th.textContent = convertToTitleCase(key);
      th.classList.add("kvps-key");

      const td = row.insertCell();

      if (Array.isArray(value)) {
        for (const item of value) {
          addValue(item);
        }
      } else {
        addValue(value);
      }

      function addValue(value) {
        if (typeof value === "object") value = JSON.stringify(value, null, 2);

        if (typeof value === "string" && value.startsWith("img://")) {
          const imgElement = document.createElement("img");
          imgElement.classList.add("kvps-img");
          imgElement.src = value.replace("img://", "/image_get?path=");
          imgElement.alt = "Image Attachment";
          td.appendChild(imgElement);

          // Add click handler and cursor change
          imgElement.style.cursor = "pointer";
          imgElement.addEventListener("click", () => {
            openImageModal(imgElement.src, 1000);
          });

          td.appendChild(imgElement);
        } else {
          const pre = document.createElement("pre");
          pre.classList.add("kvps-val");
          //   if (row.classList.contains("msg-thoughts")) {
          const span = document.createElement("span");
          span.innerHTML = escapeHTML(value);
          pre.appendChild(span);
          td.appendChild(pre);
          addCopyButtonToElement(row);

          // Add click handler
          span.addEventListener("click", () => {
            copyText(span.textContent, span);
          });

          if (window.renderMathInElement && latex) {
            renderMathInElement(span, {
              delimiters: [
                { left: "$", right: "$", display: true }
              ],
              throwOnError: false,
            });
          }
        }
      }
      //   } else {
      //     pre.textContent = value;

      //     // Add click handler
      //     pre.addEventListener("click", () => {
      //       copyText(value, pre);
      //     });

      //     td.appendChild(pre);
      //     addCopyButtonToElement(row);
      //   }
    }
    container.appendChild(table);
  }
}

function convertToTitleCase(str) {
  return str
    .replace(/_/g, " ") // Replace underscores with spaces
    .toLowerCase() // Convert the entire string to lowercase
    .replace(/\b\w/g, function (match) {
      return match.toUpperCase(); // Capitalize the first letter of each word
    });
}

function convertImageTags(content) {
  // Regular expression to match <image> tags and extract base64 content
  const imageTagRegex = /<image>(.*?)<\/image>/g;

  // Replace <image> tags with <img> tags with base64 source
  const updatedContent = content.replace(
    imageTagRegex,
    (match, base64Content) => {
      return `<img src="data:image/jpeg;base64,${base64Content}" alt="Image Attachment" style="max-width: 250px !important;"/>`;
    }
  );

  return updatedContent;
}

async function copyText(text, element) {
  try {
    await navigator.clipboard.writeText(text);
    element.classList.add("copied");
    setTimeout(() => {
      element.classList.remove("copied");
    }, 2000);
  } catch (err) {
    console.error("Failed to copy text:", err);
  }
}

function escapeHTML(str) {
  if (typeof str !== "string") {
    return str;
  }

  const escapeChars = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  };
  return str.replace(/[&<>'"]/g, (char) => escapeChars[char]);
}
