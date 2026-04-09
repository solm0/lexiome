from pydantic import BaseModel, field_validator
import re

class ClozeItem(BaseModel):
    sentence: str
    answer: str
    distractors: list[str]

    @field_validator("sentence")
    def check_single_blank(cls, v):
        if v.count("<") != 1 or v.count(">") != 1:
            raise ValueError("must contain exactly one <>")
        return v

    @field_validator("answer")
    def check_answer_in_sentence(cls, v, info):
        sentence = info.data.get("sentence", "")
        match = re.search(r"<(.*?)>", sentence)
        if not match or match.group(1) != v:
            raise ValueError("answer mismatch")
        return v

    @field_validator("distractors")
    def check_distractors(cls, v, info):
        if len(v) != 5:
            raise ValueError("must be 5 distractors")
        answer = info.data.get("answer")
        if answer in v:
            raise ValueError("distractors contain answer")
        return v