/**
 * Cognitive Panel Controller
 * Manages data loading and mutations for the cognitive training panel.
 */

import { apiClient } from '../services/api-client.js';

export interface NeuromodulatorLevel {
  name: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  description: string;
  icon: string;
}

export interface AdaptationParams {
  learningRate: number;
  explorationRate: number;
  attentionSpan: number;
  memoryConsolidation: number;
  emotionalSensitivity: number;
}

export interface ActivityLogEntry {
  message: string;
  time: string;
  icon: string;
}

export interface ParamChangeDetail {
  key: keyof AdaptationParams;
  value: number;
}

export interface CognitiveState {
  neuromodulators: NeuromodulatorLevel[];
  params: AdaptationParams;
  cognitiveLoad: number;
  sleepCycleActive: boolean;
}

interface CognitiveStateResponse {
  agent_id?: string;
  neuromodulators?: Record<string, number>;
  adaptation_params?: Record<string, number>;
  memory_stats?: Record<string, unknown>;
  last_sleep?: string | null;
  degraded?: boolean;
}

export class CognitivePanelController {
  parseAgentId(): string {
    const params = new URLSearchParams(window.location.search);
    return params.get('agent') || sessionStorage.getItem('cognitive_agent_id') || '';
  }

  async loadState(agentId: string): Promise<CognitiveState> {
    const response = (await apiClient.get(`/somabrain/cognitive/state/${agentId}`)) as CognitiveStateResponse | null;

    return {
      neuromodulators: this._mapNeuromodulators(response?.neuromodulators),
      params: this._mapParams(response?.adaptation_params),
      cognitiveLoad:
        typeof response?.memory_stats?.load === 'number' ? response.memory_stats.load : 0,
      // Preserved legacy semantics: sleep cycle is never active on initial load.
      sleepCycleActive: false,
    };
  }

  async saveParams(agentId: string, params: AdaptationParams): Promise<void> {
    await apiClient.patch(`/somabrain/cognitive/params/${agentId}`, this._toSnakeParams(params));
  }

  async triggerSleepCycle(agentId: string): Promise<{ status?: string; memories_consolidated?: number }> {
    return (await apiClient.post(`/somabrain/cognitive/sleep/${agentId}`, {
      duration_minutes: 5,
      consolidate_memory: true,
    })) as { status?: string; memories_consolidated?: number };
  }

  async resetAdaptation(agentId: string): Promise<AdaptationParams> {
    await apiClient.post(`/somabrain/cognitive/adaptation/reset/${agentId}`, {});
    return this.defaultParams();
  }

  defaultParams(): AdaptationParams {
    return {
      learningRate: 0.001,
      explorationRate: 0.15,
      attentionSpan: 0.8,
      memoryConsolidation: 0.7,
      emotionalSensitivity: 0.5,
    };
  }

  private _defaultNeuromodulators(): NeuromodulatorLevel[] {
    return [
      { name: 'Dopamine', value: 0.5, min: 0, max: 1, unit: '', description: 'Reward & Motivation', icon: 'mood' },
      { name: 'Serotonin', value: 0.5, min: 0, max: 1, unit: '', description: 'Mood & Stability', icon: 'sentiment_satisfied' },
      { name: 'Norepinephrine', value: 0.5, min: 0, max: 1, unit: '', description: 'Alertness & Focus', icon: 'electric_bolt' },
      { name: 'Acetylcholine', value: 0.5, min: 0, max: 1, unit: '', description: 'Learning & Memory', icon: 'school' },
      { name: 'GABA', value: 0.5, min: 0, max: 1, unit: '', description: 'Calm & Inhibition', icon: 'spa' },
      { name: 'Cortisol', value: 0.5, min: 0, max: 1, unit: '', description: 'Stress Response', icon: 'warning' },
    ];
  }

  private _mapNeuromodulators(input: Record<string, number> | undefined): NeuromodulatorLevel[] {
    const defaults = this._defaultNeuromodulators();
    if (!input) return defaults;
    return defaults.map((nm) => {
      const key = nm.name.toLowerCase();
      const value = input[key];
      return { ...nm, value: typeof value === 'number' ? value : 0.5 };
    });
  }

  private _mapParams(input: Record<string, number> | undefined): AdaptationParams {
    const p = input || {};
    return {
      learningRate: p.learning_rate ?? p.learningRate ?? 0.001,
      explorationRate: p.exploration_rate ?? p.explorationRate ?? 0.15,
      attentionSpan: p.attention_span ?? p.attentionSpan ?? 0.8,
      memoryConsolidation: p.memory_consolidation ?? p.memoryConsolidation ?? 0.7,
      emotionalSensitivity: p.emotional_sensitivity ?? p.emotionalSensitivity ?? 0.5,
    };
  }

  private _toSnakeParams(params: AdaptationParams): Record<string, number> {
    return {
      learning_rate: params.learningRate,
      exploration_rate: params.explorationRate,
      attention_span: params.attentionSpan,
      memory_consolidation: params.memoryConsolidation,
      emotional_sensitivity: params.emotionalSensitivity,
    };
  }
}
