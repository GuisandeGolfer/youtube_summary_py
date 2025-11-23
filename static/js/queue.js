/**
 * Queue Manager - Frontend JavaScript for managing video processing queue
 *
 * This class handles all queue-related UI interactions including:
 * - Adding videos to the queue
 * - Starting/stopping queue processing
 * - Real-time progress updates via polling
 * - Rendering queue items with status and progress
 */
class QueueManager {
    constructor() {
        this.pollInterval = null;
        this.isProcessing = false;
        this.pollIntervalMs = 2000; // Poll every 2 seconds

        // DOM element references
        this.elements = {
            queueUrl: document.getElementById('queueUrl'),
            queueList: document.getElementById('queueList'),
            queueError: document.getElementById('queueError'),
            startBtn: document.getElementById('startBtn'),
            clearBtn: document.getElementById('clearBtn'),
            addBtn: document.getElementById('addBtn'),
            // Stats elements
            statTotal: document.getElementById('statTotal'),
            statPending: document.getElementById('statPending'),
            statActive: document.getElementById('statActive'),
            statCompleted: document.getElementById('statCompleted')
        };

        // Status emoji mapping
        this.statusEmoji = {
            'pending': '⏸️',
            'downloading': '⬇️',
            'transcribing': '🎤',
            'summarizing': '📝',
            'completed': '✅',
            'failed': '❌'
        };

        this.initializeEventListeners();
    }

    /**
     * Initialize event listeners for queue controls
     */
    initializeEventListeners() {
        // Allow Enter key to add to queue
        if (this.elements.queueUrl) {
            this.elements.queueUrl.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.addToQueue();
                }
            });
        }
    }

    /**
     * Add a video URL to the queue
     */
    async addToQueue() {
        const url = this.elements.queueUrl.value.trim();

        if (!url) {
            this.showError('Please enter a YouTube URL');
            return;
        }

        this.hideError();

        try {
            const response = await fetch('/queue/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.elements.queueUrl.value = ''; // Clear input
                await this.updateQueue(); // Refresh queue display
            } else {
                this.showError(data.error || 'Failed to add to queue');
            }
        } catch (err) {
            this.showError('Network error: ' + err.message);
        }
    }

    /**
     * Start processing the queue
     */
    async startProcessing() {
        this.hideError();

        try {
            this.elements.startBtn.disabled = true;

            const response = await fetch('/queue/start', {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.isProcessing = true;
                this.startPolling(); // Start polling for updates

                // Start breathing exercise
                if (window.breathingExercise) {
                    window.breathingExercise.start();
                }
            } else {
                this.showError(data.error || 'Failed to start queue');
                this.elements.startBtn.disabled = false;
            }
        } catch (err) {
            this.showError('Network error: ' + err.message);
            this.elements.startBtn.disabled = false;
        }
    }

    /**
     * Clear all items from the queue
     */
    async clearQueue() {
        if (!confirm('Are you sure you want to clear the entire queue?')) {
            return;
        }

        this.hideError();

        try {
            const response = await fetch('/queue/clear', {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok && data.success) {
                await this.updateQueue(); // Refresh queue display
            } else {
                this.showError(data.error || 'Failed to clear queue');
            }
        } catch (err) {
            this.showError('Network error: ' + err.message);
        }
    }

    /**
     * Update queue display by fetching latest state from server
     */
    async updateQueue() {
        try {
            const response = await fetch('/queue/list');
            const data = await response.json();

            // Update stats
            this.updateStats(data.stats || {});

            // Update processing state
            this.isProcessing = data.is_processing || false;

            // Update button states
            this.updateButtonStates(data.stats || {});

            // Render queue items
            this.renderQueue(data.items || []);

            // Stop polling if processing is done
            if (!this.isProcessing && this.pollInterval) {
                this.stopPolling();
            }

        } catch (err) {
            console.error('Error updating queue:', err);
        }
    }

    /**
     * Update queue statistics display
     */
    updateStats(stats) {
        this.elements.statTotal.textContent = stats.total || 0;
        this.elements.statPending.textContent = stats.pending || 0;
        this.elements.statActive.textContent = stats.active || 0;
        this.elements.statCompleted.textContent = stats.completed || 0;
    }

    /**
     * Update button states based on queue status
     */
    updateButtonStates(stats) {
        if (this.isProcessing) {
            this.elements.startBtn.disabled = true;
            this.elements.clearBtn.disabled = true;
            this.elements.startBtn.textContent = 'Processing...';
        } else {
            this.elements.startBtn.disabled = stats.pending === 0;
            this.elements.clearBtn.disabled = stats.total === 0;
            this.elements.startBtn.textContent = 'Start Processing';

            // Stop breathing exercise when processing completes
            if (window.breathingExercise && window.breathingExercise.isRunning()) {
                window.breathingExercise.stop();
            }
        }
    }

    /**
     * Render queue items in the UI
     * @param {Array} items - Array of queue items from the server
     */
    renderQueue(items) {
        if (items.length === 0) {
            this.elements.queueList.innerHTML =
                '<div class="empty-queue">No videos in queue. Add URLs above to get started.</div>';
            return;
        }

        this.elements.queueList.innerHTML = items.map(item => {
            return this.renderQueueItem(item);
        }).join('');
    }

    /**
     * Render a single queue item
     * @param {Object} item - Queue item object
     * @returns {string} HTML string for the queue item
     */
    renderQueueItem(item) {
        const statusClass = item.status.toLowerCase();
        const title = item.title || item.url;
        const progress = item.progress || 0;
        const emoji = this.statusEmoji[item.status] || '⏳';

        return `
            <div class="queue-item ${statusClass}">
                <div class="queue-item-header">
                    <div class="queue-item-title">${emoji} ${title}</div>
                </div>
                <div class="queue-item-status">${item.current_step}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progress}%"></div>
                </div>
            </div>
        `;
    }

    /**
     * Start polling for queue updates
     */
    startPolling() {
        if (this.pollInterval) {
            return; // Already polling
        }

        this.pollInterval = setInterval(() => {
            this.updateQueue();
        }, this.pollIntervalMs);
    }

    /**
     * Stop polling for queue updates
     */
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    /**
     * Show an error message
     * @param {string} message - Error message to display
     */
    showError(message) {
        if (this.elements.queueError) {
            this.elements.queueError.textContent = message;
            this.elements.queueError.classList.add('active');
        }
    }

    /**
     * Hide the error message
     */
    hideError() {
        if (this.elements.queueError) {
            this.elements.queueError.classList.remove('active');
        }
    }

    /**
     * Initialize the queue manager (call this when the queue tab is shown)
     */
    async initialize() {
        await this.updateQueue();

        // Start polling if queue is processing
        if (this.isProcessing) {
            this.startPolling();
        }
    }

    /**
     * Cleanup when switching away from queue tab
     */
    cleanup() {
        this.stopPolling();
    }
}

// Global functions for HTML onclick handlers
// These will be called from the HTML and delegate to the queue manager instance
let queueManager = null;

function addToQueue() {
    if (queueManager) {
        queueManager.addToQueue();
    }
}

function startQueue() {
    if (queueManager) {
        queueManager.startProcessing();
    }
}

function clearQueue() {
    if (queueManager) {
        queueManager.clearQueue();
    }
}

// Initialize queue manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    queueManager = new QueueManager();

    // Initialize on page load (in case queue tab is default)
    queueManager.initialize();
});
