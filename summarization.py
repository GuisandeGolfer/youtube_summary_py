import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


def load_prompt_template() -> dict:
    """
    Load prompt template from prompt.json

    Returns:
        Dictionary containing prompt templates
    """
    try:
        prompt_file = os.path.join(os.path.dirname(__file__), "prompt.json")
        with open(prompt_file, "r") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading prompt template: {str(e)}")
        # Return default prompt if file not found
        return {
            "normal": {
                "role": "user",
                "content": "Please summarize this video transcript: {transcript}\n\nVideo URL: {url}"
            }
        }


def format_prompt(template: dict, transcript: str, url: str) -> dict:
    """
    Format prompt with transcript and URL

    Args:
        template: Prompt template dictionary
        transcript: Video transcription
        url: YouTube video URL

    Returns:
        Formatted prompt message
    """
    try:
        content = template["normal"]["content"].format(
            transcript=transcript,
            url=url
        )
        return {
            'role': template["normal"]["role"],
            'content': content
        }
    except Exception as e:
        logger.error(f"Error formatting prompt: {str(e)}")
        raise


def split_transcription(transcription: str, max_tokens: int = 2048) -> list:
    """
    Split transcription into chunks for processing

    Args:
        transcription: Full transcription text
        max_tokens: Maximum tokens per chunk

    Returns:
        List of transcription chunks
    """
    words = transcription.split()
    chunks = []
    current_chunk = []

    for word in words:
        # Rough estimation: 1 token ≈ 4 characters
        current_length = sum(len(w) for w in current_chunk) // 4

        if current_length + len(word) // 4 > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = []

        current_chunk.append(word)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def generate_summary(transcription: str, url: str) -> str:
    """
    Generate summary from video transcription using OpenAI

    Args:
        transcription: Video transcription
        url: YouTube video URL

    Returns:
        Summary text
    """
    try:
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        client = OpenAI(api_key=api_key)

        # Load prompt template
        prompt_template = load_prompt_template()

        # Split transcription into chunks if needed
        # Using gpt-4o-mini with 128K context window (using 100K to leave room for response)
        max_tokens = 100000
        chunks = split_transcription(transcription, max_tokens)

        logger.info(f"Processing {len(chunks)} chunk(s) for summarization")

        summaries = []

        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Summarizing chunk {i}/{len(chunks)}")

            # Format prompt
            prompt = format_prompt(prompt_template, chunk, url)

            # Call OpenAI API
            # Using gpt-4o-mini: faster, cheaper, and better than gpt-3.5-turbo
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[prompt],
                temperature=0.7,
                max_tokens=2000
            )

            summary = completion.choices[0].message.content
            summaries.append(summary)

        # Combine summaries
        if len(summaries) > 1:
            # If there are multiple chunks, create a final combined summary
            logger.info("Combining multiple summaries")
            combined_text = "\n\n".join(summaries)

            final_prompt = {
                'role': 'user',
                'content': f"Please create a cohesive summary from these partial summaries:\n\n{combined_text}\n\nVideo URL: {url}"
            }

            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[final_prompt],
                temperature=0.7,
                max_tokens=3000
            )

            final_summary = completion.choices[0].message.content
        else:
            final_summary = summaries[0]

        logger.info("Summary generation completed")
        return final_summary

    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise
