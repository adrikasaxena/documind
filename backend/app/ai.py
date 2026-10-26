
import httpx

from app.config import settings
from app.extractors import chunks_for_text


class OllamaError(RuntimeError):
    pass


async def generate(prompt: str) -> str:
    url = settings.ollama_base_url.rstrip("/") + "/api/chat"

    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "think": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are DocuMind, a careful document assistant. "
                    "Answer clearly and concisely using the supplied source "
                    "material for document-specific claims. If the material "
                    "does not answer the question, say so. Do not invent "
                    "facts, quotations, or citations."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "options": {
            "temperature": 0.2,
            "num_predict": 512,
        },
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(180.0, connect=5.0)
        ) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            message = data.get("message") or {}
            answer = message.get("content", "").strip()

            if not answer:
                raise OllamaError(
                    "Ollama returned an empty answer. "
                    "Check the installed model and Ollama logs."
                )

            return answer

    except httpx.ConnectError as exc:
        raise OllamaError(
            "Cannot connect to Ollama. Open Ollama and verify that "
            "the local service is running at "
            f"{settings.ollama_base_url}."
        ) from exc

    except httpx.TimeoutException as exc:
        raise OllamaError(
            "The local model timed out. Try a smaller model, "
            "shorter document context, or a lower generation limit."
        ) from exc

    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500]
        raise OllamaError(
            f"Ollama returned HTTP {exc.response.status_code}: {detail}"
        ) from exc

    except httpx.RequestError as exc:
        raise OllamaError(
            f"Could not complete the Ollama request: {exc}"
        ) from exc

    except ValueError as exc:
        raise OllamaError(
            "Ollama returned an invalid JSON response."
        ) from exc


def select_relevant_chunks(
    text: str,
    question: str,
    limit: int = 5,
) -> list[str]:
    if limit <= 0:
        return []

    chunks = chunks_for_text(text)

    if not chunks:
        return []

    terms = {
        word.lower().strip(".,?!:;()[]{}\"'")
        for word in question.split()
        if len(word) > 2
    }

    if not terms:
        return chunks[:limit]

    ranked = []

    for index, chunk in enumerate(chunks):
        lowered = chunk.lower()
        score = sum(lowered.count(term) for term in terms)
        ranked.append((score, index, chunk))

    ranked.sort(key=lambda item: (-item[0], item[1]))

    relevant = [
        chunk
        for score, _, chunk in ranked
        if score > 0
    ][:limit]

    return relevant or chunks[:limit]
