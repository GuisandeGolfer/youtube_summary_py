# Queue Feature - Action Items

## 🎯 MVP Goal
Add ability to queue multiple YouTube URLs and process them sequentially, with an engaging waiting experience.

---

## ✅ Phase 1: Core Queue (Do This First)

### Backend
- [x] Create `queue_manager.py`
  - [x] `QueueItem` dataclass (id, url, status, progress, etc.)
  - [x] `VideoQueue` class (add, remove, clear, get_next)
  - [x] Status enum (pending, downloading, transcribing, etc.)

- [x] Create `queue_processor.py`
  - [x] `QueueProcessor` class
  - [x] `process_queue()` method (loop through items)
  - [x] `process_video()` method (download → transcribe → summarize → save)
  - [x] Progress callbacks
  - [x] Error handling (skip failed videos, continue processing)

- [x] Update `app.py`
  - [x] Add queue routes:
    - [x] `POST /queue/add` - Add URL to queue
    - [x] `GET /queue/list` - Get current queue state
    - [x] `POST /queue/start` - Start processing
    - [x] `DELETE /queue/remove/<id>` - Remove item
    - [x] `POST /queue/clear` - Clear all
  - [x] Global `VideoQueue` instance
  - [x] Background thread for processing

### Frontend
- [x] Update `templates/index.html`
  - [x] Add "Queue Mode" tab/section
  - [x] Input field for URL
  - [x] "Add to Queue" button
  - [x] Queue list display
  - [x] "Start Processing" button
  - [x] Remove/Clear buttons

- [ ] Create `static/js/queue.js`
  - [ ] `QueueManager` class
  - [ ] `addToQueue(url)` method
  - [ ] `startProcessing()` method
  - [ ] `updateQueue()` method (polling)
  - [ ] `renderQueue()` method (display items)
  - [ ] Status icons and progress bars

### Testing Phase 1
- [ ] Test adding 1 URL to queue
- [ ] Test adding 5 URLs to queue
- [ ] Test processing completes successfully
- [ ] Test removing item from queue
- [ ] Test clearing queue
- [ ] Test with invalid URL (should skip and continue)

---

## ✅ Phase 2: Waiting Experience (Pick ONE)

### Option A: ASCII Snake Game 🐍 (Most Fun)
- [ ] Create `static/js/snake.js`
  - [ ] Canvas setup
  - [ ] Snake movement (arrow keys)
  - [ ] Food spawning
  - [ ] Collision detection
  - [ ] Score tracking
  - [ ] Game over / restart

- [ ] Integrate into UI
  - [ ] Show/hide game based on processing state
  - [ ] Display alongside queue progress
  - [ ] Save high score to localStorage

### Option B: Live Stats Dashboard 📊 (Most Useful)
- [ ] Create `static/js/stats.js`
  - [ ] Fetch library statistics from DB
  - [ ] Calculate:
    - [ ] Total videos processed
    - [ ] Total watch time
    - [ ] Average video length
    - [ ] Most common topics/channels
  - [ ] Real-time queue metrics:
    - [ ] Videos completed / total
    - [ ] Estimated time remaining
    - [ ] Average processing time per video

- [ ] Display in UI
  - [ ] Stats cards/panels
  - [ ] Progress visualization
  - [ ] Auto-update during processing

### Option C: Real-Time Transcription Preview 👀 (Most Unique)
- [ ] Update `queue_processor.py`
  - [ ] Stream transcription updates
  - [ ] Emit progress events with text chunks

- [ ] Create `static/js/transcription-preview.js`
  - [ ] Live text display
  - [ ] Auto-scroll
  - [ ] Typing animation effect

- [ ] Add WebSocket support (optional)
  - [ ] Or use polling with text updates

---

## ✅ Phase 3: Polish

- [ ] Error handling
  - [ ] Show error messages in UI
  - [ ] Retry failed videos option
  - [ ] Skip vs. retry logic

- [ ] UX improvements
  - [ ] Loading states
  - [ ] Success animations
  - [ ] Sound notification when complete
  - [ ] Browser notification permission

- [ ] State persistence
  - [ ] Save queue to localStorage
  - [ ] Restore queue on page refresh
  - [ ] Resume processing if interrupted

- [ ] Mobile responsive
  - [ ] Test on mobile browsers
  - [ ] Touch-friendly controls

---

## 📝 Quick Start Guide

### 1. Read the full design doc
```bash
open QUEUE_FEATURE_DESIGN.md
```

### 2. Start with Phase 1, Backend
```bash
# Create the queue manager
touch queue_manager.py
touch queue_processor.py
```

### 3. Test as you go
```bash
# Run the app and test each feature
python app.py
```

### 4. Pick your waiting experience
- Snake Game = Fun & Interactive
- Stats Dashboard = Useful & Informative
- Transcription Preview = Unique & Cool

---

## 🤔 Decision Points

### Before You Start:
1. **Which waiting experience?** (Pick one for MVP)
   - [ ] Snake Game
   - [ ] Stats Dashboard
   - [ ] Transcription Preview

2. **Sequential or Parallel processing?** (Recommend: Sequential for MVP)
   - [ ] Sequential (one at a time)
   - [ ] Parallel (2-3 at once)

3. **How to notify completion?**
   - [ ] Browser notification
   - [ ] Sound alert
   - [ ] Email (future)

---

## 📊 Progress Tracking

### Current Session Progress
- [x] **Step 1**: Created queue_manager.py with basic data structures ✓
- [x] **Step 1.5**: Database migration - added summary and created_at columns ✓
- [x] **Step 2**: Created queue_processor.py with parallel processing (2 workers) ✓
- [x] **Step 3**: Added queue routes to app.py ✓
- [x] **Step 4**: Updated frontend HTML with Queue tab and UI ✓
- [ ] **Step 5**: Add JavaScript for queue management (NEXT)
- [ ] **Step 6**: Implement waiting experience

### Phase Completion
- [ ] Phase 1 Complete (Core Queue)
- [ ] Phase 2 Complete (Waiting Experience)
- [ ] Phase 3 Complete (Polish)
- [ ] Tested with real videos
- [ ] Documentation updated
- [ ] Ready to use!

---

## 🚀 When Complete

You'll be able to:
1. Add 10 YouTube URLs to a queue
2. Hit "Process All"
3. Play a game or view stats while waiting
4. Come back to 10 transcribed and summarized videos!

**Estimated total time: 20-30 hours**

Let's build this! 🎉
