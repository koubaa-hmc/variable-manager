import os
import yaml
from typing import Dict, Any, Callable, Optional, List

class TypeDefinition:
    def __init__(self, name: str, category: str, description: str = "", default_value: Any = None, validator: Optional[Callable[[Any], bool]] = None):
        self.name = name
        self.category = category  # "generic" or "registered"
        self.description = description
        self.default_value = default_value
        self.validator = validator or (lambda v: True)

    def validate(self, value: Any) -> bool:
        try:
            return self.validator(value)
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "default_value": self.default_value
        }


class TypeRegistry:
    def __init__(self, palettes_dir: str = "types"):
        self.types: Dict[str, TypeDefinition] = {}
        self.palettes_dir = palettes_dir
        self._register_default_types()
        self.load_palettes()

    def register(self, type_def: TypeDefinition):
        self.types[type_def.name] = type_def

    def get(self, name: str) -> Optional[TypeDefinition]:
        return self.types.get(name)

    def list_types(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.types.values()]

    def validate_value(self, type_name: str, value: Any) -> bool:
        t_def = self.get(type_name)
        if not t_def:
            return True
        return t_def.validate(value)

    def get_default_value(self, type_name: str) -> Any:
        t_def = self.get(type_name)
        if t_def and t_def.default_value is not None:
            return t_def.default_value
        # Fallbacks based on category/type
        if type_name == "string":
            return ""
        elif type_name in ("number", "integer"):
            return 0
        elif type_name == "boolean":
            return False
        elif type_name == "array":
            return []
        elif type_name == "object":
            return {}
        return None

    def load_palettes(self):
        """
        Load independent LinkML Type Palette YAML files from the palettes directory.
        Following TestStand best practices, type palettes define custom data types,
        slots, and default values (ifabsent).
        """
        paths_to_check = [
            self.palettes_dir,
            os.path.join(os.getcwd(), self.palettes_dir),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", self.palettes_dir))
        ]

        target_dir = None
        for p in paths_to_check:
            if os.path.exists(p) and os.path.isdir(p):
                target_dir = p
                break

        if not target_dir:
            return

        for filename in os.listdir(target_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(target_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        schema = yaml.safe_load(f)
                        if schema and isinstance(schema, dict) and "classes" in schema:
                            classes = schema["classes"]
                            for class_name, class_info in classes.items():
                                desc = class_info.get("description", "")
                                slot_usage = class_info.get("slot_usage", {})
                                
                                # Construct default instance or default value from LinkML slot_usage ifabsent
                                default_val = {}
                                slot_list = class_info.get("slots", [])
                                
                                for slot_name in slot_list:
                                    s_cfg = slot_usage.get(slot_name, {})
                                    raw_default = s_cfg.get("ifabsent")
                                    
                                    # Parse string representations of defaults if needed
                                    parsed_val = raw_default
                                    if isinstance(raw_default, str):
                                        if raw_default.startswith("[") and raw_default.endswith("]"):
                                            try:
                                                import ast
                                                parsed_val = ast.literal_eval(raw_default)
                                            except Exception:
                                                pass
                                        elif raw_default.replace(".", "", 1).isdigit():
                                            parsed_val = float(raw_default) if "." in raw_default else int(raw_default)
                                        elif raw_default.lower() == "true":
                                            parsed_val = True
                                        elif raw_default.lower() == "false":
                                            parsed_val = False
                                            
                                    default_val[slot_name] = parsed_val

                                # If class has single slot like 'values' or 'device_id', simplify default representation if appropriate
                                if len(slot_list) == 1:
                                    single_slot = slot_list[0]
                                    if single_slot in ("values", "device_id"):
                                        default_val = default_val.get(single_slot)

                                # Define validator for LinkML-defined registered type
                                def make_validator(s_list, s_usage):
                                    def validator(v):
                                        if len(s_list) == 1 and s_list[0] in ("values", "device_id"):
                                            return True
                                        return isinstance(v, dict)
                                    return validator

                                self.register(TypeDefinition(
                                    name=class_name,
                                    category="registered",
                                    description=desc,
                                    default_value=default_val,
                                    validator=make_validator(slot_list, slot_usage)
                                ))
                except Exception as e:
                    print(f"Error loading LinkML palette {filepath}: {e}")

    def _register_default_types(self):
        # Generics
        self.register(TypeDefinition("string", "generic", "Text string value", "", lambda v: isinstance(v, str)))
        self.register(TypeDefinition("number", "generic", "Floating point or integer number", 0.0, lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)))
        self.register(TypeDefinition("integer", "generic", "Integer number", 0, lambda v: isinstance(v, int) and not isinstance(v, bool)))
        self.register(TypeDefinition("boolean", "generic", "Boolean true/false", False, lambda v: isinstance(v, bool)))
        self.register(TypeDefinition("array", "generic", "List / array collection", [], lambda v: isinstance(v, list)))
        self.register(TypeDefinition("object", "generic", "Key-value dictionary object", {}, lambda v: isinstance(v, dict)))

