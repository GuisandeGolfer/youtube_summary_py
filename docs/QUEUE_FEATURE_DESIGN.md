# Queue Feature & Waiting Experience Design

## 📋 Table of Contents
1. [Feature Overview](#feature-overview)
2. [Queue Implementation](#queue-implementation)
3. [Waiting Experience Ideas](#waiting-experience-ideas)
4. [UI/UX Design](#uiux-design)
5. [Technical Implementation](#technical-implementation)
6. [Development Roadmap](#development-roadmap)

---

## Feature Overview

### Current Flow
```
User enters 1 URL → Download → Transcribe → Summarize → Save → Done
```

### New Flow
```
User enters multiple URLs → Queue them → Hit "Process Queue" →
Background processing (download/transcribe/summarize each) →
Show waiting experience while processing →
Display results as they complete
```

### Key Requirements
- ✅ Add multiple URLs to a queue
- ✅ Process videos sequentially (or in parallel)
- ✅ Show progress for each video
- ✅ Keep user engaged during wait time
- ✅ Handle errors gracefully (skip failed videos, continue queue)
- ✅ Allow queue management (add, remove, reorder)

---

## Queue Implementation

### Queue Data Structure

```python
queue_item = {
    'id': uuid.uuid4(),
    'url': 'https://youtube.com/...',
    'status': 'pending',  # pending, downloading, transcribing, summarizing, completed, failed
    'progress': 0,        # 0-100%
    'current_step': '',   # "Downloading audio...", "Transcribing...", etc.
    'error': None,
    'title': '',
    'duration': 0,
    'added_at': datetime.now()
}
```

### Processing Strategies

#### Option 1: Sequential Processing (Recommended for MVP)
**Pros:**
- Simple to implement
- Lower resource usage
- Predictable behavior
- Easier error handling

**Cons:**
- Slower overall completion time
- One failure could block others (but we'll skip failures)

```python
for item in queue:
    try:
        process_video(item)
    except Exception as e:
        item.status = 'failed'
        item.error = str(e)
        continue  # Skip to next video
```

#### Option 2: Parallel Processing (Future Enhancement)
**Pros:**
- Faster overall completion
- Better resource utilization

**Cons:**
- More complex
- Higher resource usage
- Need to manage concurrent downloads/transcriptions

```python
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(process_video, item): item for item in queue}
```

### Progress Tracking

Each video goes through stages:
1. **Downloading** (0-25%)
2. **Transcribing** (25-75%)
3. **Summarizing** (75-95%)
4. **Saving** (95-100%)

Real-time updates to UI via:
- WebSocket (for live updates)
- Or polling (simpler, check status every 2-3 seconds)

---

## Waiting Experience Ideas

### 🎮 Interactive Games (Ranked by Implementation Difficulty)

#### 1. **ASCII Snake Game** ⭐ (Easy - Recommended)
**Why:** Classic, simple, engaging, works in terminal or web

```
┌─────────────────────┐
│ Score: 15           │
│                     │
│    ●●●●●           │
│        ●           │
│        ●    ◉      │
│                    │
│ Controls: ↑↓←→    │
└─────────────────────┘
```

**Implementation:**
- Canvas-based (web) or curses (terminal)
- Simple collision detection
- Score tracking
- ~200 lines of code

#### 2. **Typing Speed Test** ⭐ (Easy)
**Why:** Productive, improves skills, naturally timed

```
Type this quote:
"The quick brown fox..."

Your typing: The quick br_

WPM: 45 | Accuracy: 98% | Time: 1:23
```

**Features:**
- Random programming quotes
- WPM calculation
- Accuracy tracking
- Leaderboard (local storage)

#### 3. **Trivia Quiz** ⭐⭐ (Medium)
**Why:** Educational, customizable topics

```
Question 3/10

What year was Python created?
A) 1989
B) 1991 ✓
C) 1995
D) 2000

Correct! Score: 3/3
```

**Topics:**
- Programming trivia
- YouTube/tech history
- General knowledge
- Video content (questions about their own videos!)

#### 4. **Wordle Clone** ⭐⭐ (Medium)
**Why:** Popular, perfect 5-10 min duration

```
Guess the word (5 letters):

Attempt 1: STORY
🟩⬜⬜🟨⬜

Attempt 2: S_ _ _ _
```

#### 5. **2048 Game** ⭐⭐⭐ (Hard)
**Why:** Addictive, good for longer waits

```
┌──────────────────┐
│  2  4  8  16    │
│  4  8  16 32    │
│  8  16 32 64    │
│ 16 32 64 128    │
│                  │
│ Score: 1024      │
└──────────────────┘
```

### 📊 Data Visualization / Analytics

#### 6. **Live Video Stats Dashboard** ⭐ (Easy - Very Cool!)
**Why:** Useful, shows progress, educational

```
┌─ Queue Progress ────────────────────┐
│                                     │
│ ████████████░░░░░░ 60% Complete    │
│                                     │
│ Videos Processed: 3/5               │
│ Total Duration: 2h 15m              │
│ Avg Processing Time: 8m per video  │
│                                     │
│ Your Library Stats:                 │
│ ├─ Total Videos: 47                │
│ ├─ Total Watch Time: 18h 32m       │
│ ├─ Most Common Topic: Python (12)  │
│ └─ Longest Video: "3hr Tutorial"   │
└─────────────────────────────────────┘
```

#### 7. **Real-Time Transcription Preview** ⭐⭐ (Medium - Unique!)
**Why:** Shows actual progress, interesting to watch

```
Currently Transcribing: "How to Build..."
─────────────────────────────────────────
...so in this video we're going to learn
about building RESTful APIs using Flask.
First, we'll set up our environment...
                                      ▌ (live cursor)

Progress: 34% | Duration: 24:15
```

### 🎨 Ambient/Relaxing

#### 8. **ASCII Art Animations** ⭐ (Easy)
**Why:** Relaxing, low effort

```
Frame 1:        Frame 2:        Frame 3:
   ☁️              ☁️    ☁️           ☁️
  ☁️  ☁️         ☁️      ☁️         ☁️
    🌊🌊           🌊🌊🌊          🌊🌊
```

Themes:
- Ocean waves
- Rain/weather
- Space/stars
- Matrix-style falling code

#### 9. **Breathing Exercise** ⭐ (Easy - Wellness!)
**Why:** Productive, reduces anxiety, healthy

```
┌────────────────────────┐
│                        │
│      Breathe In        │
│                        │
│         ●●●            │
│       ●●●●●●●          │
│         ●●●            │
│                        │
│   Hold: ▓▓▓▓▓░░░       │
└────────────────────────┘

4-7-8 Technique
Inhale: 4s → Hold: 7s → Exhale: 8s
```

### 🎯 Productivity

#### 10. **Mini Code Challenges** ⭐⭐⭐ (Hard - Advanced Users)
**Why:** Educational, productive

```
Challenge: Reverse a string without using reverse()

def reverse(s):
    # Your code here
    return _____

Test: reverse("hello") → "olleh"

Submit  Skip  Hint
```

#### 11. **Random Tech Facts / Quotes** ⭐ (Very Easy)
**Why:** Simple, educational, requires no interaction

```
┌─────────────────────────────────┐
│  💡 Did You Know?               │
│                                 │
│  The first YouTube video was   │
│  uploaded on April 23, 2005.   │
│  It was titled "Me at the zoo"│
│                                 │
│  Processing video 2/5...  40%  │
└─────────────────────────────────┘
```

### 🎲 My Top 3 Recommendations

#### **#1: ASCII Snake Game + Live Stats** ⭐⭐⭐⭐⭐
**Combination of games + useful info**
- Top: Live processing stats
- Middle: Snake game
- Bottom: Progress bar

**Why:**
- Engaging but not distracting
- Easy to stop/start
- Shows progress alongside fun
- Easy to implement

#### **#2: Real-Time Transcription Preview** ⭐⭐⭐⭐
**Watch the AI work in real-time**

**Why:**
- Unique and fascinating
- Educational
- Shows actual progress
- Makes wait time feel productive

#### **#3: Typing Speed Test** ⭐⭐⭐⭐
**Productive and engaging**

**Why:**
- Improves actual skills
- Natural timing
- Can be stopped anytime
- Simple to implement
- Competitive (beat your best)

---

## UI/UX Design

### New UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  YouTube Video Queue Processor                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Add Videos to Queue:                                       │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ https://youtube.com/watch?v=...                       │ │
│  └───────────────────────────────────────────────────────┘ │
│  [Add to Queue]                                            │
│                                                             │
│  ┌─ Queue (5 videos) ───────────────────────────────────┐ │
│  │                                                        │ │
│  │ ✓ How to Python              [8:23]  Completed        │ │
│  │ ▶ Building REST APIs         [24:15] Transcribing 45%│ │
│  │ ⏸ Machine Learning Basics   [45:00] Pending          │ │
│  │ ⏸ Docker Tutorial            [18:30] Pending          │ │
│  │ ⏸ Git Advanced Topics        [32:10] Pending          │ │
│  │                                                        │ │
│  │ [Remove] [Clear All]                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  [Start Processing] [Pause] [Cancel]                       │
│                                                             │
│  ┌─ While You Wait ─────────────────────────────────────┐ │
│  │                                                        │ │
│  │   🎮 Play Snake Game                                  │ │
│  │   📊 View Your Stats                                  │ │
│  │   👀 Watch Live Transcription                         │ │
│  │   💡 Read Random Facts                                │ │
│  │                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Status Indicators

```python
STATUS_ICONS = {
    'pending': '⏸',
    'downloading': '⬇️',
    'transcribing': '🎤',
    'summarizing': '📝',
    'completed': '✓',
    'failed': '❌'
}
```

### Progress Display Options

#### Option 1: Detailed View
```
Video 2/5: "Building REST APIs"
├─ Download:   ████████████████████ 100% ✓
├─ Transcribe: ████████████░░░░░░░░  65% ▶
├─ Summarize:  ░░░░░░░░░░░░░░░░░░░░   0%
└─ Save:       ░░░░░░░░░░░░░░░░░░░░   0%

Elapsed: 4:32 | Estimated: 2:45 remaining
```

#### Option 2: Compact View
```
[2/5] Building REST APIs ████████░░ 65% (Transcribing...)
```

---

## Technical Implementation

### Backend Architecture

#### Queue Manager (New Module)

```python
# queue_manager.py

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import uuid
from datetime import datetime

class VideoStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class QueueItem:
    id: str
    url: str
    status: VideoStatus
    progress: int  # 0-100
    current_step: str
    error: Optional[str] = None
    title: str = ""
    duration: int = 0
    added_at: datetime = None

    def __post_init__(self):
        if self.added_at is None:
            self.added_at = datetime.now()

class VideoQueue:
    def __init__(self):
        self.items: List[QueueItem] = []
        self.is_processing = False

    def add(self, url: str) -> QueueItem:
        """Add video to queue"""
        item = QueueItem(
            id=str(uuid.uuid4()),
            url=url,
            status=VideoStatus.PENDING,
            progress=0,
            current_step="Waiting in queue..."
        )
        self.items.append(item)
        return item

    def remove(self, item_id: str) -> bool:
        """Remove video from queue"""
        self.items = [item for item in self.items if item.id != item_id]
        return True

    def clear(self):
        """Clear entire queue"""
        self.items = []

    def get_next_pending(self) -> Optional[QueueItem]:
        """Get next pending video"""
        for item in self.items:
            if item.status == VideoStatus.PENDING:
                return item
        return None

    def update_progress(self, item_id: str, progress: int, step: str):
        """Update progress for specific item"""
        for item in self.items:
            if item.id == item_id:
                item.progress = progress
                item.current_step = step
                break
```

#### Queue Processor

```python
# queue_processor.py

import asyncio
from queue_manager import VideoQueue, VideoStatus
from youtube import download_video_audio
from transcription import transcribe_audio_file
from summarization import generate_summary
from database import save_transcription_to_db

class QueueProcessor:
    def __init__(self, queue: VideoQueue, on_progress_callback=None):
        self.queue = queue
        self.on_progress = on_progress_callback
        self.should_stop = False

    async def process_queue(self):
        """Process all pending videos in queue"""
        self.queue.is_processing = True

        while True:
            if self.should_stop:
                break

            item = self.queue.get_next_pending()
            if not item:
                break  # No more pending items

            try:
                await self.process_video(item)
                item.status = VideoStatus.COMPLETED
                item.progress = 100

            except Exception as e:
                item.status = VideoStatus.FAILED
                item.error = str(e)
                # Continue to next video instead of stopping

        self.queue.is_processing = False

    async def process_video(self, item: QueueItem):
        """Process a single video"""

        # Step 1: Download (0-25%)
        item.status = VideoStatus.DOWNLOADING
        self._update_progress(item, 5, "Starting download...")

        filename = download_video_audio(item.url, AUDIO_PATH)
        item.title = filename  # Update with actual title
        self._update_progress(item, 25, "Download complete")

        # Step 2: Transcribe (25-75%)
        item.status = VideoStatus.TRANSCRIBING
        self._update_progress(item, 30, "Starting transcription...")

        transcription = transcribe_audio_file(filename, AUDIO_PATH)
        self._update_progress(item, 75, "Transcription complete")

        # Step 3: Summarize (75-95%)
        item.status = VideoStatus.SUMMARIZING
        self._update_progress(item, 80, "Generating summary...")

        summary = generate_summary(transcription, item.url)
        self._update_progress(item, 95, "Summary complete")

        # Step 4: Save (95-100%)
        self._update_progress(item, 98, "Saving to database...")
        save_transcription_to_db(
            db_path=DB_PATH,
            transcription=transcription,
            video_url=item.url,
            summary=summary
        )
        self._update_progress(item, 100, "Complete!")

    def _update_progress(self, item: QueueItem, progress: int, step: str):
        """Update progress and notify callback"""
        item.progress = progress
        item.current_step = step

        if self.on_progress:
            self.on_progress(item)

    def stop(self):
        """Stop processing queue"""
        self.should_stop = True
```

### Frontend Updates

#### New Flask Routes

```python
# app.py additions

from queue_manager import VideoQueue, QueueItem
from queue_processor import QueueProcessor

# Global queue instance
video_queue = VideoQueue()
processor = None

@app.route('/queue/add', methods=['POST'])
def add_to_queue():
    """Add video URL to queue"""
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    item = video_queue.add(url)

    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'url': item.url,
            'status': item.status.value
        }
    })

@app.route('/queue/list', methods=['GET'])
def list_queue():
    """Get current queue"""
    return jsonify({
        'items': [
            {
                'id': item.id,
                'url': item.url,
                'status': item.status.value,
                'progress': item.progress,
                'current_step': item.current_step,
                'title': item.title,
                'error': item.error
            }
            for item in video_queue.items
        ],
        'is_processing': video_queue.is_processing
    })

@app.route('/queue/start', methods=['POST'])
def start_queue():
    """Start processing queue"""
    global processor

    if video_queue.is_processing:
        return jsonify({'error': 'Queue already processing'}), 400

    processor = QueueProcessor(video_queue)

    # Run in background thread
    import threading
    thread = threading.Thread(target=asyncio.run, args=(processor.process_queue(),))
    thread.start()

    return jsonify({'success': True, 'message': 'Queue processing started'})

@app.route('/queue/remove/<item_id>', methods=['DELETE'])
def remove_from_queue(item_id):
    """Remove item from queue"""
    video_queue.remove(item_id)
    return jsonify({'success': True})

@app.route('/queue/clear', methods=['POST'])
def clear_queue():
    """Clear entire queue"""
    video_queue.clear()
    return jsonify({'success': True})
```

#### Frontend JavaScript (New)

```javascript
// static/js/queue.js

class QueueManager {
    constructor() {
        this.items = [];
        this.pollInterval = null;
    }

    async addToQueue(url) {
        const response = await fetch('/queue/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url})
        });
        return response.json();
    }

    async startProcessing() {
        await fetch('/queue/start', {method: 'POST'});
        this.startPolling();
    }

    startPolling() {
        this.pollInterval = setInterval(() => {
            this.updateQueue();
        }, 2000); // Poll every 2 seconds
    }

    async updateQueue() {
        const response = await fetch('/queue/list');
        const data = await response.json();

        this.items = data.items;
        this.renderQueue();

        // Stop polling if queue is done
        if (!data.is_processing) {
            this.stopPolling();
        }
    }

    renderQueue() {
        const container = document.getElementById('queue-list');
        container.innerHTML = this.items.map(item => `
            <div class="queue-item status-${item.status}">
                <div class="item-title">${item.title || item.url}</div>
                <div class="item-progress">
                    <div class="progress-bar" style="width: ${item.progress}%"></div>
                </div>
                <div class="item-status">${item.current_step}</div>
            </div>
        `).join('');
    }
}
```

---

## Development Roadmap

### Phase 1: Core Queue Functionality (Week 1)
- [ ] Create `queue_manager.py` with QueueItem and VideoQueue classes
- [ ] Create `queue_processor.py` with sequential processing
- [ ] Add queue management routes to Flask app
- [ ] Update database schema if needed
- [ ] Basic UI for adding/viewing queue

### Phase 2: UI Enhancement (Week 2)
- [ ] Improve queue display with status icons
- [ ] Add drag-and-drop URL input
- [ ] Implement progress bars
- [ ] Add remove/clear queue buttons
- [ ] Real-time updates via polling or WebSocket

### Phase 3: Waiting Experience - MVP (Week 3)
**Choose ONE to implement first:**

**Option A: Snake Game** (Fun, Interactive)
- [ ] Implement ASCII/Canvas snake game
- [ ] Add score tracking
- [ ] Integrate into waiting screen

**Option B: Live Stats Dashboard** (Useful, Informative)
- [ ] Calculate library statistics
- [ ] Create real-time stats display
- [ ] Show queue progress metrics

**Option C: Real-Time Transcription Preview** (Unique, Cool)
- [ ] Stream transcription as it happens
- [ ] Display in real-time window
- [ ] Add auto-scroll

### Phase 4: Polish & Additional Features (Week 4)
- [ ] Error handling and retry logic
- [ ] Pause/resume queue processing
- [ ] Queue persistence (save queue state)
- [ ] Email/notification when queue completes
- [ ] Add 2-3 more waiting experiences
- [ ] User preference for waiting experience

### Phase 5: Advanced Features (Future)
- [ ] Parallel processing (2-3 videos at once)
- [ ] Priority queue
- [ ] Scheduled processing (process at specific time)
- [ ] Batch operations (process playlist)
- [ ] Export queue results

---

## Implementation Checklist

### Backend
- [ ] `queue_manager.py` - Queue data structure
- [ ] `queue_processor.py` - Processing logic
- [ ] Update `app.py` with queue routes
- [ ] Add background task processing
- [ ] Error handling for individual videos
- [ ] Progress tracking callbacks

### Frontend
- [ ] New HTML template with queue UI
- [ ] JavaScript for queue management
- [ ] Real-time progress updates
- [ ] Waiting experience container
- [ ] Responsive design for mobile

### Waiting Experience (Pick 1 for MVP)
- [ ] **Snake Game** - `static/js/snake.js`
- [ ] **Stats Dashboard** - `static/js/stats.js`
- [ ] **Transcription Preview** - Update processor to stream updates

### Testing
- [ ] Test with 1 video
- [ ] Test with 5 videos
- [ ] Test with failed video (invalid URL)
- [ ] Test pause/resume
- [ ] Test browser refresh (state persistence)

### Documentation
- [ ] Update README with queue feature
- [ ] Add usage examples
- [ ] Document API endpoints
- [ ] Create troubleshooting guide

---

## Questions to Consider

1. **Processing Strategy**: Sequential or parallel? (Recommend: Sequential for MVP)
2. **Waiting Experience**: Which game/feature first? (Recommend: Snake or Live Stats)
3. **State Persistence**: Save queue state to DB or just in-memory? (Recommend: In-memory for MVP)
4. **Notifications**: How to notify when complete? (Browser notification, email, sound?)
5. **Error Handling**: Skip failed videos or pause entire queue? (Recommend: Skip and continue)
6. **UI Framework**: Vanilla JS or add React/Vue? (Recommend: Vanilla JS for simplicity)

---

## Estimated Time

- **Phase 1 (Core Queue)**: 8-10 hours
- **Phase 2 (UI Enhancement)**: 6-8 hours
- **Phase 3 (Waiting Experience)**: 4-6 hours (for one game/feature)
- **Phase 4 (Polish)**: 4-6 hours

**Total MVP**: 22-30 hours

**With all features**: 40-50 hours

---

## Next Steps

1. **Review this document** - Which approach appeals to you?
2. **Pick waiting experience** - Snake game, stats, or transcription preview?
3. **Start with Phase 1** - Get basic queue working first
4. **Iterate** - Add features incrementally

Let me know which direction you want to go, and we can start implementing! 🚀
