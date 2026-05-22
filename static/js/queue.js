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
            queueAction: document.getElementById('queueAction'),
            queueQuality: document.getElementById('queueQuality'),
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

        // Animation preference
        this.selectedAnimation = this.loadAnimationPreference();

        this.initializeEventListeners();
        this.initAnimationSelector();
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
     * Load animation preference from localStorage
     */
    loadAnimationPreference() {
        const saved = localStorage.getItem('waitingAnimation');
        if (saved) {
            return saved;
        }
        // Random default: 50/50 chance
        return Math.random() < 0.5 ? 'breathing' : 'waves';
    }

    /**
     * Save animation preference to localStorage
     */
    saveAnimationPreference(value) {
        localStorage.setItem('waitingAnimation', value);
        this.selectedAnimation = value;
    }

    /**
     * Initialize animation selector radio buttons
     */
    initAnimationSelector() {
        const breathingRadio = document.getElementById('animBreathing');
        const wavesRadio = document.getElementById('animWaves');

        if (!breathingRadio || !wavesRadio) return;

        // Set initial selection
        if (this.selectedAnimation === 'breathing') {
            breathingRadio.checked = true;
        } else {
            wavesRadio.checked = true;
        }

        // Add change listeners
        breathingRadio.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.saveAnimationPreference('breathing');
                this.switchAnimation('breathing');
            }
        });

        wavesRadio.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.saveAnimationPreference('waves');
                this.switchAnimation('waves');
            }
        });
    }

    /**
     * Switch between animations (can happen mid-processing)
     */
    switchAnimation(type) {
        // Stop both animations
        if (window.breathingExercise && window.breathingExercise.isRunning()) {
            window.breathingExercise.stop();
        }
        if (window.waveAnimation && window.waveAnimation.isActive) {
            window.waveAnimation.stop();
        }

        // Start selected animation if queue is processing
        if (this.isProcessing) {
            if (type === 'breathing' && window.breathingExercise) {
                window.breathingExercise.start();
            } else if (type === 'waves' && window.waveAnimation) {
                window.waveAnimation.start();
            }
        }
    }

    /**
     * Add a video URL to the queue
     */
    async addToQueue() {
        const url = this.elements.queueUrl.value.trim();
        const actionType = this.elements.queueAction.value;
        const quality = this.elements.queueQuality.value;

        if (!url) {
            this.showError('Please enter a YouTube URL');
            return;
        }

        this.hideError();

        try {
            const requestBody = {
                url,
                action_type: actionType,
                quality: quality
            };

            const response = await fetch('/queue/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
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

                // Start selected animation
                if (this.selectedAnimation === 'breathing' && window.breathingExercise) {
                    window.breathingExercise.start();
                } else if (this.selectedAnimation === 'waves' && window.waveAnimation) {
                    window.waveAnimation.start();
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

            // Stop both animations when processing completes
            if (window.breathingExercise && window.breathingExercise.isRunning()) {
                window.breathingExercise.stop();
            }
            if (window.waveAnimation && window.waveAnimation.isActive) {
                window.waveAnimation.stop();
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

        this.elements.queueList.innerHTML = items.map((item, index) => {
            return this.renderQueueItem(item, index);
        }).join('');

        // Add holographic mouse tracking to all queue items
        this.addHolographicEffects();
    }

    /**
     * Add mouse tracking effects to queue items for 3D tilt
     */
    addHolographicEffects() {
        const queueItems = document.querySelectorAll('.queue-item');

        queueItems.forEach(item => {
            item.addEventListener('mousemove', (e) => {
                const rect = item.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateX = (y - centerY) / 10;
                const rotateY = (centerX - x) / 10;

                // Apply 3D transform
                item.style.transform = `
                    perspective(1000px)
                    rotateX(${rotateX}deg)
                    rotateY(${rotateY}deg)
                    scale3d(1.02, 1.02, 1.02)
                `;

                // Move holographic gradient based on mouse position
                const percentX = (x / rect.width) * 100;
                const percentY = (y / rect.height) * 100;

                const before = item.querySelector('::before');
                if (item.style) {
                    item.style.setProperty('--mouse-x', `${percentX}%`);
                    item.style.setProperty('--mouse-y', `${percentY}%`);
                }
            });

            item.addEventListener('mouseleave', () => {
                item.style.transform = `
                    perspective(1000px)
                    rotateX(0deg)
                    rotateY(0deg)
                    scale3d(1, 1, 1)
                `;
            });
        });
    }

    /**
     * Render a single queue item
     * @param {Object} item - Queue item object
     * @param {number} index - Index in the queue for staggered animation
     * @returns {string} HTML string for the queue item
     */
    renderQueueItem(item, index = 0) {
        const statusClass = item.status.toLowerCase();
        const title = item.title || item.url;
        const progress = item.progress || 0;
        const emoji = this.statusEmoji[item.status] || '⏳';

        // Action type badge
        const actionType = item.action_type || 'process';
        const badgeClass = actionType === 'download' ? 'badge-download' : 'badge-process';
        const badgeText = actionType === 'download' ? `DL: ${item.quality}` : 'Process';

        // Staggered animation delay
        const animationDelay = index * 0.1;

        return `
            <div class="queue-item ${statusClass}" style="animation-delay: ${animationDelay}s">
                <div class="sparkle"></div>
                <div class="queue-item-header">
                    <div class="queue-item-title">
                        ${emoji} ${title}
                        <span class="queue-item-badge ${badgeClass}">${badgeText}</span>
                    </div>
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

function toggleQueueQuality() {
    const action = document.getElementById('queueAction').value;
    const qualityGroup = document.getElementById('queueQualityGroup');

    if (action === 'download') {
        qualityGroup.style.display = 'block';
    } else {
        qualityGroup.style.display = 'none';
    }
}

/**
 * Toggle wave animation (called from HTML onclick)
 */
function toggleWaves() {
    if (window.waveAnimation) {
        window.waveAnimation.toggle();
    }
}

// Initialize queue manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    queueManager = new QueueManager();

    // Initialize on page load (in case queue tab is default)
    queueManager.initialize();
});
