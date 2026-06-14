/**
 * SaaS Tenant Wizard Steps
 *
 * Renders the wizard stepper / navigation header.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('saas-tenant-wizard-steps')
export class SaasTenantWizardSteps extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .progress {
            display: flex;
            padding: 16px 32px;
            gap: 8px;
            border-bottom: 1px solid #f0f0f0;
        }

        .step {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }

        .step-indicator {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #e0e0e0;
            color: #666;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 600;
        }

        .step.active .step-indicator {
            background: #1a1a1a;
            color: #fff;
        }

        .step.completed .step-indicator {
            background: #16a34a;
            color: #fff;
        }

        .step-label {
            font-size: 12px;
            color: #666;
        }

        .step.active .step-label {
            color: #1a1a1a;
            font-weight: 500;
        }
    `;

    @property({ type: Number }) currentStep = 1;
    @property({ type: Array }) steps: string[] = ['Identity', 'Plan', 'Defaults', 'Review'];

    render() {
        return html`
            <div class="progress">
                ${this.steps.map((step, i) => {
                    const stepNumber = i + 1;
                    const isActive = stepNumber === this.currentStep;
                    const isCompleted = stepNumber < this.currentStep;
                    return html`
                        <div class="step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}">
                            <div class="step-indicator">${isCompleted ? '✓' : stepNumber}</div>
                            <span class="step-label">${step}</span>
                        </div>
                    `;
                })}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-wizard-steps': SaasTenantWizardSteps;
    }
}
