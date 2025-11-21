# Transcript Viewer CLI Setup Guide

## What This Does

The `transcript_viewer.py` script lets you:
- 📋 Browse all your saved YouTube transcriptions
- 🔍 Search and select videos using fzf (with preview!)
- 📊 See metadata: duration, channel, date added
- 📝 Get summary or full transcription
- 📋 Output to stdout or clipboard

## Installation

### 1. Install fzf (if not already installed)
```bash
brew install fzf
```

### 2. Make the script executable (already done)
```bash
chmod +x transcript_viewer.py
```

### 3. Add aliases to your ~/.zshrc

Add these lines to the end of `~/.zshrc`:

```bash
# YouTube Transcript Viewer (separate from main app)
alias transcript="$HOME/Desktop/PARA/Projects_1/youtube_summary_py/transcript_viewer.py"
alias gettranny="$HOME/Desktop/PARA/Projects_1/youtube_summary_py/transcript_viewer.py"
```

### 4. Reload your shell
```bash
source ~/.zshrc
```

## Usage Examples

### Basic usage (interactive)
```bash
transcript
```
This will:
1. Show all videos in fzf with metadata
2. Let you preview video details
3. Ask if you want summary or transcription
4. Output to stdout

### Get summary directly
```bash
transcript --summary
```
Still lets you select video, but skips asking for type.

### Get full transcription
```bash
transcript --full
```

### Copy to clipboard
```bash
transcript --clipboard
```
Copies result to clipboard (macOS pbcopy).

### Combination flags
```bash
transcript --summary --clipboard
```
Get summary and copy to clipboard.

### Pipe to clipboard yourself
```bash
transcript | pbcopy
```
or with your custom `clip` command:
```bash
transcript | clip
```

### Pipe to other tools

The script automatically formats output with logical line breaks (one sentence per line, wrapping long sentences at 100 chars), making it perfect for piping:

```bash
# Preview first 10 sentences
transcript | head -10

# Preview first 20 sentences
transcript --full | head -20

# See last 5 sentences
transcript | tail -5

# Save to file (formatted with line breaks)
transcript --full > notes.txt

# Search within result
transcript --summary | grep "important"

# Count sentences (approximately)
transcript --full | wc -l

# Count words
transcript --full | wc -w

# View in pager with nice formatting
transcript --full | less
```

## fzf Display Format

The fzf selection shows:
- `[ID]` - Video ID
- `[Duration]` - Length in MM:SS or HH:MM:SS
- Title (truncated to 60 chars)
- Channel name (truncated to 25 chars)
- Date added
- `[S]` - Has summary available
- `[T]` - Has transcription available

## fzf Navigation

- `↑/↓` or `j/k` - Navigate videos
- `Enter` - Select video
- `Esc` or `Ctrl-C` - Cancel
- Type to search/filter videos
- `Ctrl-N/Ctrl-P` - Alternative navigation

## Flags Reference

| Flag | Description |
|------|-------------|
| `--summary` | Get summary (skip type selection) |
| `--full` | Get full transcription (skip type selection) |
| `--clipboard` | Copy to clipboard instead of stdout |
| `-h, --help` | Show help message |

## Error Handling

- If database doesn't exist: Shows error and exits
- If no videos in database: Shows message to process some videos first
- If fzf not installed: Shows installation instructions
- If selected video has no content: Shows error
- If clipboard fails: Falls back to stdout

## Examples in Practice

```bash
# Quick workflow: get summary and copy
transcript --summary --clipboard

# Review full transcription in less
transcript --full | less

# Save specific video's summary
transcript --summary > video-notes.md

# Search for specific topic across transcription
transcript --full | grep -i "machine learning"

# Get summary and paste into other app
transcript --summary --clipboard
# Then Cmd+V in other app
```

## Tips

1. **Search while browsing**: In fzf, just start typing to filter
2. **Preview pane**: Move up/down to see different video details
3. **Pipe-friendly**: Default stdout makes it easy to pipe to other tools
4. **Fast access**: Use the short alias `gettranny` for speed

## Troubleshooting

**"fzf not found"**
```bash
brew install fzf
```

**"Database not found"**
- Make sure you've processed at least one video with the main app
- Check that `transcriptions.db` exists in the project directory

**"pbcopy not found" (Linux)**
Replace `pbcopy` with `xclip` in the script:
```bash
# Install xclip
sudo apt install xclip

# Or modify the script to use xclip
```

**Permission denied**
```bash
chmod +x transcript_viewer.py
```

## What's Next?

The script is ready to use! Try:
```bash
transcript
```

Enjoy your quick access to transcriptions! 🚀
