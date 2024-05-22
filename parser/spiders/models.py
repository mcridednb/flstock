import json
from typing import Dict, Any

from pydantic import BaseModel, model_validator


class ExtraMixin(BaseModel):
    def dict(self, *args, **kwargs):
        return json.loads(self.json(*args, **kwargs))

    extra: Dict[str, Any]

    @model_validator(mode="before")
    def build_extra(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        all_required_field_names = {
            field.alias or field_name
            for field_name, field in cls.__fields__.items()
            if (field.alias or field_name) != "extra"
        }

        extra: Dict[str, Any] = {}
        for field_name in list(values):
            if field_name not in all_required_field_names:
                extra[field_name] = values.pop(field_name)
        values["extra"] = extra
        return values
