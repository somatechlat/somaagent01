/**
 * Settings Controller
 * Manages data loading, mutation, save, and export logic for the settings view.
 */

import { apiClient } from '../services/api-client.js';

export interface ModelConfig {
  provider: string;
  model: string;
  contextWindow: number;
  maxTokens: number;
}

export interface FeatureFlags {
  voiceEnabled: boolean;
  memoryEnabled: boolean;
  toolsEnabled: boolean;
  mcpEnabled: boolean;
}

export interface SettingsData {
  chatModel: ModelConfig;
  utilityModel: ModelConfig;
  featureFlags: FeatureFlags;
}

export interface SettingsControllerHost {
  requestUpdate(): void;
}

export class SettingsController {
  private _host: SettingsControllerHost;

  private _chatModel: ModelConfig = {
    provider: 'openai',
    model: 'gpt-4-turbo',
    contextWindow: 128000,
    maxTokens: 4096,
  };

  private _utilityModel: ModelConfig = {
    provider: 'anthropic',
    model: 'claude-3-haiku',
    contextWindow: 200000,
    maxTokens: 2048,
  };

  private _featureFlags: FeatureFlags = {
    voiceEnabled: true,
    memoryEnabled: true,
    toolsEnabled: true,
    mcpEnabled: false,
  };

  private _isDirty = false;
  private _isSaving = false;

  constructor(host: SettingsControllerHost) {
    this._host = host;
  }

  get chatModel(): ModelConfig {
    return this._chatModel;
  }

  get utilityModel(): ModelConfig {
    return this._utilityModel;
  }

  get featureFlags(): FeatureFlags {
    return this._featureFlags;
  }

  get isDirty(): boolean {
    return this._isDirty;
  }

  get isSaving(): boolean {
    return this._isSaving;
  }

  updateChatModel(field: keyof ModelConfig, value: string | number): void {
    this._chatModel = { ...this._chatModel, [field]: value };
    this._isDirty = true;
    this._host.requestUpdate();
  }

  updateUtilityModel(field: keyof ModelConfig, value: string | number): void {
    this._utilityModel = { ...this._utilityModel, [field]: value };
    this._isDirty = true;
    this._host.requestUpdate();
  }

  toggleFlag(flag: keyof FeatureFlags): void {
    this._featureFlags = {
      ...this._featureFlags,
      [flag]: !this._featureFlags[flag],
    };
    this._isDirty = true;
    this._host.requestUpdate();
  }

  async loadSettings(): Promise<void> {
    try {
      const data = await apiClient.get<Partial<SettingsData>>('/settings/agent/');
      if (data.chatModel) {
        this._chatModel = data.chatModel;
      }
      if (data.utilityModel) {
        this._utilityModel = data.utilityModel;
      }
      if (data.featureFlags) {
        this._featureFlags = data.featureFlags;
      }
      this._host.requestUpdate();
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  }

  async saveSettings(): Promise<void> {
    this._isSaving = true;
    this._host.requestUpdate();

    try {
      await apiClient.put('/settings/agent/', {
        chatModel: this._chatModel,
        utilityModel: this._utilityModel,
        featureFlags: this._featureFlags,
      });
      this._isDirty = false;
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      this._isSaving = false;
      this._host.requestUpdate();
    }
  }

  exportConfig(): void {
    const config = {
      chatModel: this._chatModel,
      utilityModel: this._utilityModel,
      featureFlags: this._featureFlags,
      exportedAt: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'agent-config.json';
    a.click();
    URL.revokeObjectURL(url);
  }
}
