/**
 * Audit Progress Polling Component
 * Polls audit progress and updates UI in real-time.
 */
class AuditProgressPoller {
    constructor(auditId, options = {}) {
        this.auditId = auditId;
        this.pollInterval = options.pollInterval || 3000;
        this.maxRetries = options.maxRetries || 3;
        this.onProgress = options.onProgress || (() => {});
        this.onComplete = options.onComplete || (() => {});
        this.onError = options.onError || (() => {});
        
        this.retryCount = 0;
        this.currentInterval = this.pollInterval;
        this.timerId = null;
        this.isRunning = false;
        this.startTime = null;
    }

    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        this.startTime = Date.now();
        this.poll();
    }

    stop() {
        this.isRunning = false;
        if (this.timerId) {
            clearTimeout(this.timerId);
            this.timerId = null;
        }
    }

    async poll() {
        if (!this.isRunning) return;

        try {
            const response = await fetch(`/audit/${this.auditId}/progress`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            this.retryCount = 0;
            this.currentInterval = this.pollInterval;

            this.updateProgressBar(data.progress_pct || 0);
            this.updateModuleStatus(data.modules || []);
            this.updateTimeEstimate(data.estimated_remaining_seconds);

            this.onProgress(data);

            if (data.status === 'completed' || data.status === 'failed') {
                this.stop();
                this.onComplete(data);
                return;
            }

            this.scheduleNextPoll();
        } catch (error) {
            this.handleError(error);
        }
    }

    handleError(error) {
        this.retryCount++;
        
        if (this.retryCount >= this.maxRetries) {
            this.stop();
            this.onError(new Error(`Max retries (${this.maxRetries}) exceeded: ${error.message}`));
            return;
        }

        this.currentInterval = this.pollInterval * Math.pow(2, this.retryCount);
        this.onError(error);
        this.scheduleNextPoll();
    }

    scheduleNextPoll() {
        if (!this.isRunning) return;
        this.timerId = setTimeout(() => this.poll(), this.currentInterval);
    }

    updateProgressBar(pct) {
        const progressBar = document.querySelector('[data-progress-bar]');
        const progressText = document.querySelector('[data-progress-text]');
        
        if (progressBar) {
            progressBar.style.width = `${pct}%`;
        }
        if (progressText) {
            progressText.textContent = `${Math.round(pct)}%`;
        }
    }

    updateModuleStatus(modules) {
        if (!modules || !modules.length) return;

        modules.forEach(module => {
            const moduleName = module.module_name || module.name;
            const card = document.querySelector(`[data-module="${moduleName}"]`);
            if (!card) return;

            card.className = `module-status-${module.status} border rounded-lg p-4`;

            const statusText = card.querySelector('[data-module-status-text]');
            if (statusText) {
                statusText.textContent = module.status;
            }

            const progressBar = card.querySelector('[data-module-progress]');
            if (progressBar) {
                progressBar.style.width = `${module.progress_pct || 0}%`;
            }
        });
    }

    getStatusIcon(status) {
        switch (status) {
            case 'completed':
                return '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>';
            case 'running':
                return '<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>';
            case 'failed':
                return '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>';
            default:
                return '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><circle cx="10" cy="10" r="3"/></svg>';
        }
    }

    getStatusClass(status) {
        switch (status) {
            case 'completed': return 'text-green-400';
            case 'running': return 'text-blue-400';
            case 'failed': return 'text-red-400';
            default: return 'text-gray-500';
        }
    }

    updateTimeEstimate(seconds) {
        const elapsedEl = document.querySelector('[data-elapsed-time]');
        const remainingEl = document.querySelector('[data-remaining-time]');
        
        if (elapsedEl && this.startTime) {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            elapsedEl.textContent = this.formatTime(elapsed);
        }
        
        if (remainingEl && seconds !== undefined && seconds !== null) {
            remainingEl.textContent = this.formatTime(seconds);
        }
    }

    formatTime(seconds) {
        if (seconds < 60) return `${seconds}s`;
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}m ${secs}s`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('[data-audit-progress]');
    if (!container) return;

    const auditId = container.dataset.auditId;
    if (!auditId) return;

    const poller = new AuditProgressPoller(auditId, {
        onProgress: (data) => {
            const statusEl = document.querySelector('[data-audit-status]');
            if (statusEl) {
                statusEl.textContent = data.status;
            }
        },
        onComplete: (data) => {
            window.location.reload();
        },
        onError: (err) => {
            console.error('Audit progress polling error:', err);
        }
    });

    poller.start();
    window.auditPoller = poller;
});
