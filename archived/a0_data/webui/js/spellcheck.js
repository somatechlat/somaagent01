// spellcheck.js – client‑side spell checking for the chat input
// Uses Typo.js (Hunspell) and the en_US dictionary placed in /a0/webui/dictionaries

// Load the dictionary asynchronously
async function loadDictionary() {
    const [aff, dic] = await Promise.all([
        fetch('dictionaries/en_US.aff').then(r => r.text()),
        fetch('dictionaries/en_US.dic').then(r => r.text())
    ]);
    // Typo constructor: new Typo(lang, affData, dicData, options)
    return new Typo('en_US', aff, dic, { platform: 'any' });
}

let typoInstance = null;
loadDictionary().then(dict => {
    typoInstance = dict;
    console.log('Spell‑check dictionary loaded, words:', typoInstance.dictionarySize);
}).catch(err => console.error('Failed to load dictionary for spell‑check:', err));

// Helper: get up to 5 suggestions for a word
function getSuggestions(word) {
    if (!typoInstance) return [];
    if (typoInstance.check(word)) return [];
    return typoInstance.suggest(word).slice(0, 5);
}

// UI handling – we will attach to the textarea with id="chat-input"
const chatInput = document.getElementById('chat-input');
if (!chatInput) {
    console.warn('Spell‑check: chat input element not found');
}

// Create a container for suggestions (simple dropdown below the textarea)
const suggBox = document.createElement('div');
suggBox.id = 'spell-suggestions';
suggBox.style.position = 'absolute';
suggBox.style.background = '#fffae6';
suggBox.style.border = '1px solid #ccc';
suggBox.style.padding = '2px 4px';
suggBox.style.borderRadius = '3px';
suggBox.style.display = 'none';
suggBox.style.zIndex = '1000';
document.body.appendChild(suggBox);

let debounceTimer;
chatInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(checkSpelling, 300);
});

function checkSpelling() {
    const text = chatInput.value;
    const words = text.split(/\s+/).filter(w => w.length);
    const lastWord = words[words.length - 1] || '';
    const cleanWord = lastWord.replace(/[^a-zA-Z']/g, '');
    const suggestions = getSuggestions(cleanWord);
    renderSuggestions(suggestions, cleanWord);
}

function renderSuggestions(list, original) {
    // Position the box under the textarea (simple approximation)
    const rect = chatInput.getBoundingClientRect();
    suggBox.style.left = `${rect.left + window.scrollX}px`;
    suggBox.style.top = `${rect.bottom + window.scrollY + 2}px`;
    suggBox.innerHTML = '';
    if (!list.length) {
        suggBox.style.display = 'none';
        return;
    }
    list.forEach(s => {
        const span = document.createElement('span');
        span.textContent = s;
        span.style.cursor = 'pointer';
        span.style.marginRight = '4px';
        span.onclick = () => replaceWord(original, s);
        suggBox.appendChild(span);
    });
    suggBox.style.display = 'block';
}

function replaceWord(oldWord, newWord) {
    const cursorPos = chatInput.selectionStart;
    const before = chatInput.value.slice(0, cursorPos);
    const after = chatInput.value.slice(cursorPos);
    const newBefore = before.replace(new RegExp(`\\b${oldWord}\\b$`), newWord + ' ');
    chatInput.value = newBefore + after;
    const newPos = newBefore.length;
    chatInput.setSelectionRange(newPos, newPos);
    suggBox.style.display = 'none';
    chatInput.focus();
}
