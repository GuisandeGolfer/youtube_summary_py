# AI YouTube FOMO Utility

## TLDR;

> give this script a link to a YouTube video, and it will ask ChatGPT for detailed summary of the video.
> Saving you the time of actually watching it.

### Steps Completed so Far:

1. [x] recieve link to youtube video.
2. [x] download youtube video audio.
3. [x] transcribe audio file through OpenAI library API call.
4. [x] send a prompt to ChatGPT with transcription of content.
5. [x] Create a new repo and a read-me with a video that explains how it works.
6. [ ] getting an error while using py-tube (only workarounds on StackOverflow)
    - switch the script from using pytube and use yt-dlp python lib instead.

### Things to improve later on:

1. [ ] since the api key is being loaded in from *password-store*, I may have to enter the encryption key after time passes
2. [ ] maybe add an ASCII moving loading screen while the API calls are happening?
    - some kind of fun animation
3. [ ] create a chrome extension for this?
    - Youtube AI summarizer
4. [ ] or make a website that has a one-time payment for a license to use a web interface that stores their summaries,
        "watch" history, and all they need is a one-time payment of $50 (rate limit API calls and do cost analysis).
5. [ ] buy ShipFast as a template for releasing the SaaS. ($169 - $199)
6. [ ] have the option to give it a youtube playlist, and iterate the process of summarizing videos
            - maybe create a playlist mega-summary.
