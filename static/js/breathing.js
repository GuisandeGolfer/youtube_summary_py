/**
 * Breathing Exercise Manager
 *
 * 4-4-6-2 Breathing Pattern:
 * - Breathe In: 4 seconds
 * - Hold: 4 seconds
 * - Breathe Out: 6 seconds
 * - Hold: 2 seconds
 */

class BreathingExercise {
    constructor() {
        // Breathing pattern configuration (4-4-6-2)
        this.phases = [
            { name: 'Breathe In', duration: 4, className: 'inhale' },
            { name: 'Hold', duration: 4, className: 'hold' },
            { name: 'Breathe Out', duration: 6, className: 'exhale' },
            { name: 'Hold', duration: 2, className: 'hold-out' }
        ];

        this.currentPhaseIndex = 0;
        this.timeRemaining = this.phases[0].duration;
        this.cycleCount = 0;
        this.isActive = false;
        this.isPaused = false;
        this.intervalId = null;

        // DOM elements
        this.elements = {
            container: document.getElementById('breathingContainer'),
            circle: document.getElementById('breathingCircle'),
            text: document.getElementById('breathingText'),
            timer: document.getElementById('breathingTimer'),
            phase: document.getElementById('breathingPhase'),
            cycleCount: document.getElementById('breathingCycleCount'),
            toggleBtn: document.getElementById('breathingToggle')
        };
    }

    /**
     * Start the breathing exercise
     */
    start() {
        if (this.isActive) return;

        this.isActive = true;
        this.isPaused = false;
        this.cycleCount = 1;
        this.currentPhaseIndex = 0;
        this.timeRemaining = this.phases[0].duration;

        // Show the container
        if (this.elements.container) {
            this.elements.container.style.display = 'block';
        }

        // Start the breathing cycle
        this.updateDisplay();
        this.startTimer();
    }

    /**
     * Stop the breathing exercise
     */
    stop() {
        this.isActive = false;
        this.isPaused = false;
        this.clearTimer();

        // Hide the container
        if (this.elements.container) {
            this.elements.container.style.display = 'none';
        }

        // Reset display
        this.resetDisplay();
    }

    /**
     * Toggle pause/resume
     */
    toggle() {
        if (!this.isActive) return;

        this.isPaused = !this.isPaused;

        if (this.isPaused) {
            this.clearTimer();
            if (this.elements.toggleBtn) {
                this.elements.toggleBtn.textContent = 'Resume';
            }
        } else {
            this.startTimer();
            if (this.elements.toggleBtn) {
                this.elements.toggleBtn.textContent = 'Pause';
            }
        }
    }

    /**
     * Start the countdown timer
     */
    startTimer() {
        this.clearTimer();

        this.intervalId = setInterval(() => {
            if (this.isPaused) return;

            this.timeRemaining--;

            if (this.timeRemaining < 0) {
                // Move to next phase
                this.nextPhase();
            }

            this.updateDisplay();
        }, 1000);
    }

    /**
     * Clear the timer
     */
    clearTimer() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    /**
     * Move to the next breathing phase
     */
    nextPhase() {
        this.currentPhaseIndex++;

        // If we've completed all phases, start a new cycle
        if (this.currentPhaseIndex >= this.phases.length) {
            this.currentPhaseIndex = 0;
            this.cycleCount++;
        }

        // Reset time for new phase
        this.timeRemaining = this.phases[this.currentPhaseIndex].duration;
    }

    /**
     * Update the display with current breathing state
     */
    updateDisplay() {
        const currentPhase = this.phases[this.currentPhaseIndex];

        // Update text
        if (this.elements.text) {
            this.elements.text.textContent = currentPhase.name;
        }

        // Update timer
        if (this.elements.timer) {
            this.elements.timer.textContent = this.timeRemaining;
        }

        // Update phase description
        if (this.elements.phase) {
            this.elements.phase.textContent = `Phase: ${currentPhase.name} (${currentPhase.duration}s)`;
        }

        // Update cycle count
        if (this.elements.cycleCount) {
            this.elements.cycleCount.textContent = this.cycleCount;
        }

        // Update circle class for animation
        if (this.elements.circle) {
            // Remove all phase classes
            this.phases.forEach(phase => {
                this.elements.circle.classList.remove(phase.className);
            });

            // Add current phase class
            this.elements.circle.classList.add(currentPhase.className);
        }
    }

    /**
     * Reset the display to initial state
     */
    resetDisplay() {
        if (this.elements.circle) {
            this.phases.forEach(phase => {
                this.elements.circle.classList.remove(phase.className);
            });
        }

        if (this.elements.text) {
            this.elements.text.textContent = 'Breathe In';
        }

        if (this.elements.timer) {
            this.elements.timer.textContent = '4';
        }

        if (this.elements.phase) {
            this.elements.phase.textContent = 'Phase: Breathe In (4s)';
        }

        if (this.elements.cycleCount) {
            this.elements.cycleCount.textContent = '1';
        }

        if (this.elements.toggleBtn) {
            this.elements.toggleBtn.textContent = 'Pause';
        }
    }

    /**
     * Check if breathing exercise is currently active
     */
    isRunning() {
        return this.isActive;
    }
}

// Initialize breathing exercise when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.breathingExercise = new BreathingExercise();
});

// Global function for toggle button
function toggleBreathing() {
    if (window.breathingExercise) {
        window.breathingExercise.toggle();
    }
}
