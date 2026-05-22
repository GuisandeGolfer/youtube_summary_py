/**
 * Wave Animation - ASCII Art ocean wave animation for waiting experience
 *
 * This class provides a relaxing wave animation that cycles through 6 frames
 * showing waves crashing against the beach. It follows the same architectural
 * pattern as the breathing exercise.
 */
class WaveAnimation {
    constructor() {
        // Animation configuration
        this.currentFrame = 0;
        this.isActive = false;
        this.isPaused = false;
        this.intervalId = null;
        this.frameDelay = 500; // 500ms per frame (dynamic pace)

        // Cache DOM elements
        this.elements = {
            container: document.getElementById('waveContainer'),
            canvas: document.getElementById('waveCanvas'),
            toggleBtn: document.getElementById('waveToggle')
        };

        // 6 ASCII art frames showing wave cycle
        this.frames = this.createFrames();

        // Pre-render all frames with color spans
        this.renderedFrames = this.frames.map(frame => this.colorizeFrame(frame));
    }

    /**
     * Create the 6 wave animation frames
     * Each frame is approximately 50 chars wide × 12 lines tall
     */
    createFrames() {
        return [
            // Frame 1: Calm Sea
            {
                name: 'Calm Sea',
                art: `                      sun
  bird                                      bird


  water≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈water
 water∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼water
water˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜water
sand░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░sand
sand▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒sand
sand....................................sand`
            },

            // Frame 2: Building
            {
                name: 'Building',
                art: `                      sun
  bird                                    bird

                          foam°
  water≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈foam°foam≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈water
 water∼∼∼∼∼∼∼∼∼∼∼∼∼∼foam*foam*foam∼∼∼∼∼∼∼∼∼∼∼∼∼water
water˜˜˜˜˜˜˜˜˜˜˜˜foam·foam·foam·foam˜˜˜˜˜˜˜˜˜˜˜water
sand░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░sand
sand▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒sand
sand....................................sand`
            },

            // Frame 3: Cresting
            {
                name: 'Cresting',
                art: `                      sun
                                         bird
                     foam*foam*
              foam°foam*foam*foam*foam°
  water≈≈≈≈≈foam*foam*foam˚foam*foam*foam≈≈≈≈≈≈water
 water∼∼∼foam·foam·foam·foam·foam·foam·foam∼∼∼∼water
water˜˜foam˚foam˚foam˚foam˚foam˚foam˚foam˚foam˜water
sand░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░sand
sand▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒sand
sand....................................sand`
            },

            // Frame 4: Breaking
            {
                name: 'Breaking',
                art: `                      sun

           foam*foam*foam*foam*foam*
      foam°foam*foam*foam*foam*foam*foam°
 foam°foam*foam*foam˚foam˚foam*foam*foam*foam°
foam·foam·foam·foam·foam·foam·foam·foam·foam·foam
water˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜water
sand░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░sand
sand▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒sand
sand....................................sand`
            },

            // Frame 5: Washing
            {
                name: 'Washing',
                art: `                      sun
  bird

         foam°foam°foam°foam°foam°
    foam·foam·foam·foam·foam·foam·foam
  foam˚foam˚foam˚foam˚foam˚foam˚foam˚foam
water∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼water
sand░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░sand
sand▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒sand
sand....................................sand`
            },

            // Frame 6: Receding
            {
                name: 'Receding',
                art: `                      sun
  bird                                    bird


            foam·foam·foam·
       foam˚foam˚foam˚foam˚foam
  water∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼water
 water˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜˜water
sand░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░sand
sand▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒sand
sand....................................sand`
            }
        ];
    }

    /**
     * Colorize a frame by wrapping characters in appropriate CSS class spans
     * @param {Object} frame - Frame object with art property
     * @returns {string} HTML string with colored spans
     */
    colorizeFrame(frame) {
        let html = '';
        let inWord = false;
        let currentWord = '';
        let currentClass = '';

        const lines = frame.art.split('\n');

        for (let line of lines) {
            for (let char of line) {
                // Detect semantic markers (word boundaries)
                if (char === ' ') {
                    // Space - output current word if any, then space
                    if (inWord) {
                        html += this.wrapInClass(currentWord, currentClass);
                        currentWord = '';
                        inWord = false;
                    }
                    html += ' ';
                } else if (this.isSemanticMarker(char)) {
                    // Found a marker - determine class
                    const newClass = this.getClassForMarker(char);

                    if (newClass !== currentClass) {
                        // Class changed - output previous word if any
                        if (inWord) {
                            html += this.wrapInClass(currentWord, currentClass);
                            currentWord = '';
                        }
                        currentClass = newClass;
                    }

                    inWord = true;
                    currentWord += char;
                } else {
                    // Regular character - add to current word
                    if (!inWord) {
                        inWord = true;
                        currentClass = 'wave-text';
                    }
                    currentWord += char;
                }
            }

            // End of line - output remaining word
            if (inWord) {
                html += this.wrapInClass(currentWord, currentClass);
                currentWord = '';
                inWord = false;
            }

            html += '\n';
        }

        return html;
    }

    /**
     * Check if character is a semantic marker
     */
    isSemanticMarker(char) {
        const markers = '~≈∼˜*°·˚░▒.v^><○◉';
        return markers.includes(char);
    }

    /**
     * Get CSS class for a marker character
     */
    getClassForMarker(char) {
        // Water characters
        if ('~≈∼˜'.includes(char)) return 'wave-water';
        // Foam characters
        if ('*°·˚'.includes(char)) return 'wave-foam';
        // Sand characters
        if ('░▒.'.includes(char)) return 'wave-sand';
        // Bird characters
        if ('v^><'.includes(char)) return 'wave-bird';
        // Sun/moon
        if ('○◉'.includes(char)) return 'wave-sun';

        return 'wave-text';
    }

    /**
     * Wrap text in a CSS class span
     */
    wrapInClass(text, className) {
        if (!text) return '';
        if (className === 'wave-text') return text;
        return `<span class="${className}">${text}</span>`;
    }

    /**
     * Start the wave animation
     */
    start() {
        if (this.isActive) return;

        this.isActive = true;
        this.isPaused = false;
        this.currentFrame = 0;

        // Show container
        if (this.elements.container) {
            this.elements.container.style.display = 'block';
        }

        // Update initial display
        this.render();

        // Start animation timer
        this.startTimer();

        // Update button text
        this.updateButtonText();
    }

    /**
     * Stop the wave animation
     */
    stop() {
        this.isActive = false;
        this.isPaused = false;

        // Clear interval
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }

        // Hide container
        if (this.elements.container) {
            this.elements.container.style.display = 'none';
        }

        // Reset frame
        this.currentFrame = 0;
    }

    /**
     * Toggle pause/resume
     */
    toggle() {
        if (!this.isActive) return;

        this.isPaused = !this.isPaused;
        this.updateButtonText();
    }

    /**
     * Start the animation timer
     */
    startTimer() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        this.intervalId = setInterval(() => {
            if (this.isPaused) return;

            this.nextFrame();
            this.render();
        }, this.frameDelay);
    }

    /**
     * Advance to next frame
     */
    nextFrame() {
        this.currentFrame = (this.currentFrame + 1) % this.frames.length;
    }

    /**
     * Render current frame to canvas
     */
    render() {
        if (!this.elements.canvas) return;

        const frameHTML = this.renderedFrames[this.currentFrame];
        this.elements.canvas.innerHTML = frameHTML;
    }

    /**
     * Update button text based on state
     */
    updateButtonText() {
        if (!this.elements.toggleBtn) return;

        this.elements.toggleBtn.textContent = this.isPaused ? 'Resume' : 'Pause';
    }

    /**
     * Check if animation is running
     */
    isRunning() {
        return this.isActive && !this.isPaused;
    }
}

// Initialize wave animation when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.waveAnimation = new WaveAnimation();
});
