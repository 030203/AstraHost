from dataclasses import dataclass


@dataclass(frozen=True)
class SkillResolution:
    name: str
    description: str
    system_prompt: str
    tool_names: tuple[str, ...] = ()


class Skill:
    name = ""
    description = ""

    def matches(self, message):
        raise NotImplementedError

    def resolve(self, message):
        raise NotImplementedError


class KeywordSkill(Skill):
    def __init__(self, name, description, keywords, tool_names, system_prompt):
        self.name = name
        self.description = description
        self.keywords = tuple(str(keyword).lower() for keyword in keywords if str(keyword).strip())
        self.tool_names = tuple(tool_names)
        self.system_prompt = system_prompt

    def matches(self, message):
        normalized = (message or "").strip().lower()
        return any(keyword in normalized for keyword in self.keywords)

    def resolve(self, message):
        return SkillResolution(
            name=self.name,
            description=self.description,
            system_prompt=self.system_prompt,
            tool_names=self.tool_names,
        )
