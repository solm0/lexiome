from pydantic import BaseModel, field_validator
import re

class ClozeItem(BaseModel):
    sentence: str
    distractors: list[str]

    @field_validator("sentence")
    def check_no_placeholder(cls, v):
        import re
        match = re.search(r"<(.*?)>", v)
        if not match:
            raise ValueError("no blank found")

        word = match.group(1).lower()
        if word in ["word", "noun", "verb", "adj"]:
            raise ValueError("invalid placeholder")

        return v

    @field_validator("distractors")
    def check_distractors(cls, v):
        if len(v) != 5:
            raise ValueError("must be 5 distractors")
        return v

    def get_answer(self):
        import re
        return re.search(r"<(.*?)>", self.sentence).group(1)