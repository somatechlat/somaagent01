/**
 * Theme Loader Module
 * Per SRS AGENTSKIN.md Section 5.2
 * 
 * Thin bridge between UI Core and SomaAgentSkin SDK
 */

const THEMES_PATH = '/static/themes/';
const CONFIG_KEY = 'ui-config';

const Theme = {
    currentSkin: null,

    async init(name = null) {
        const config = this.getConfig();
        const skinName = name || config.theme || 'default';
        await this.use(skinName);
    },

    async use(nameOrUrl, options = {}) {
        try {
            const skin = nameOrUrl.startsWith('http')
                ? await this.loadRemote(nameOrUrl)
                : await this.loadLocal(nameOrUrl, options);

            if (this.validate(skin)) {
                this.apply(skin);
                this.currentSkin = skin;
                return true;
            }
        } catch (e) {
            console.warn('Failed to load skin:', nameOrUrl, e);
            return false;
        }
    },

    async loadLocal(name, options = {}) {
        const basePath = options.basePath || THEMES_PATH;
        const url = `${basePath}${name}.json`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Skin not found: ${name}`);
        return res.json();
    },

    async loadRemote(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Remote skin fetch failed: ${url}`);
        return res.json();
    },

    validate(skin) {
        if (!skin || typeof skin !== 'object') return false;
        if (!skin.name || typeof skin.name !== 'string') return false;
        if (!skin.variables || typeof skin.variables !== 'object') return false;
        return true;
    },

    apply(skin) {
        const root = document.documentElement;
        const vars = skin.variables || {};

        for (const [key, value] of Object.entries(vars)) {
            const prop = key.startsWith('--') ? key : `--${key}`;
            root.style.setProperty(prop, value);
        }
    },

    async switch(name) {
        const success = await this.use(name);
        if (success) {
            this.saveConfig({ theme: name });
        }
        return success;
    },

    getConfig() {
        try {
            const stored = localStorage.getItem(CONFIG_KEY);
            return stored ? JSON.parse(stored) : {};
        } catch {
            return {};
        }
    },

    saveConfig(updates) {
        const config = { ...this.getConfig(), ...updates };
        localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
    },

    setTheme(mode) {
        document.documentElement.setAttribute('data-theme', mode);
        this.saveConfig({ mode });
    },

    toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'light' ? 'dark' : 'light';
        this.setTheme(next);
        return next;
    }
};

export default Theme;

if (typeof window !== 'undefined') {
    window.Theme = Theme;
}
