from typing import Dict, Any, Callable, Optional, List

class TypeDefinition:
    def __init__(self, name: str, category: str, description: str = "", validator: Optional[Callable[[Any], bool]] = None):
        self.name = name
        self.category = category  # "generic" or "registered"
        self.description = description
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
            "description": self.description
        }


class TypeRegistry:
    def __init__(self):
        self.types: Dict[str, TypeDefinition] = {}
        self._register_default_types()

    def register(self, type_def: TypeDefinition):
        self.types[type_def.name] = type_def

    def get(self, name: str) -> Optional[TypeDefinition]:
        return self.types.get(name)

    def list_types(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.types.values()]

    def validate_value(self, type_name: str, value: Any) -> bool:
        t_def = self.get(type_name)
        if not t_def:
            # If type is unknown, default to valid or strict (let's be permissive or return True if not found, or False)
            return True
        return t_def.validate(value)

    def _register_default_types(self):
        # Generics
        self.register(TypeDefinition("string", "generic", "Text string value", lambda v: isinstance(v, str)))
        self.register(TypeDefinition("number", "generic", "Floating point or integer number", lambda v: isinstance(v, (int, float) and not isinstance(v, bool))))
        self.register(TypeDefinition("integer", "generic", "Integer number", lambda v: isinstance(v, int) and not isinstance(v, bool)))
        self.register(TypeDefinition("boolean", "generic", "Boolean true/false", lambda v: isinstance(v, bool)))
        self.register(TypeDefinition("array", "generic", "List / array collection", lambda v: isinstance(v, list)))
        self.register(TypeDefinition("object", "generic", "Key-value dictionary object", lambda v: isinstance(v, dict)))

        # Registered Robotics / Domain Types
        self.register(TypeDefinition(
            "JointAngles", 
            "registered", 
            "Robot joint angles representation (list of numbers)", 
            lambda v: isinstance(v, list) and all(isinstance(x, (int, float)) for x in v)
        ))
        self.register(TypeDefinition(
            "Pose", 
            "registered", 
            "Cartesian pose (position [x, y, z] and orientation [qx, qy, qz, qw] or Euler)", 
            lambda v: isinstance(v, dict) and any(k in v for k in ["position", "orientation", "x", "y", "z"])
        ))
        self.register(TypeDefinition(
            "DeviceReference", 
            "registered", 
            "Reference to a concrete device or station identifier", 
            lambda v: isinstance(v, str) and len(v) > 0
        ))
