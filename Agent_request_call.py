from typing import Optional
import chardet
import Agent_orchestrator


def bytes_to_string(file_content: Optional[bytes]) -> Optional[str]:
    if file_content is None:
        return None
    detected = chardet.detect(file_content)
    encoding = detected.get("encoding", "utf-8")
    return file_content.decode(encoding, errors="replace")


def agent_request_process(
    prompt_text: str,
    file_content: Optional[bytes] = None
) -> str:
    if file_content:
        file_str = bytes_to_string(file_content)
        answer = Agent_orchestrator.agent_process_request(
            prompt_text=prompt_text,
            file_content=file_str
        )
    else:
        answer = Agent_orchestrator.agent_process_request(
            prompt_text=prompt_text,
            file_content=None
        )

    if answer is None:
        return "The agent returned no answer."
    if not isinstance(answer, str):
        return str(answer)
    return answer


# NEW: Creative reaction request (image + headline + personas)
def creative_reaction_request_process(
    headline: str,
    personas_json: str,
    image_bytes: bytes,
    image_mime: str = "image/png"
) -> str:
    answer = Agent_orchestrator.creative_reaction_process_request(
        headline=headline,
        personas_json=personas_json,
        image_bytes=image_bytes,
        image_mime=image_mime
    )
    if answer is None:
        return "The creative reaction agent returned no answer."
    if not isinstance(answer, str):
        return str(answer)
    return answer