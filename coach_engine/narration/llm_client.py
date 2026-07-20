from openai import OpenAI
import os


DEFAULT_MODEL = "gpt-4.1-mini"


def generate_text(prompt, model=DEFAULT_MODEL):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable bulunamadı. "
            "Önce terminalde OPENAI_API_KEY tanımla."
        )

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    return response.output_text