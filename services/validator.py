import re


def validate(result: dict, lemma: str) -> bool:
    if "content" not in result:
        return False

    sentences = result["content"]

    if not isinstance(sentences, list) or len(sentences) != 6:
        return False

    valid_count = 0

    for s in sentences:
        if not isinstance(s, str):
            continue

        # 최소 길이 체크
        if len(s) < 5:
            continue

        # <> 포함 여부 (soft)
        if "<" in s and ">" in s:
            valid_count += 1
        else:
            valid_count += 0.5  # 완전 실패는 아님

    # 절반 이상이면 통과
    return valid_count >= 3