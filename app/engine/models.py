from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class AttributeModifiers(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    strength: int = Field(default=0, alias="str")
    dexterity: int = Field(default=0, alias="dex")
    constitution: int = Field(default=0, alias="con")
    intelligence: int = Field(default=0, alias="int")
    wisdom: int = Field(default=0, alias="wis")
    charisma: int = Field(default=0, alias="cha")

class Proficiency(BaseModel):
    rank: int = 0       # 0=Untrained, 2=Trained, 4=Expert, 6=Master, 8=Legendary
    modifier: int = 0   # rank + level + attribute_mod

class Defenses(BaseModel):
    ac: int = 10
    hp: int = 0
    shield_bonus: int = 0
    fortitude: Proficiency = Field(default_factory=Proficiency)
    reflex: Proficiency = Field(default_factory=Proficiency)
    will: Proficiency = Field(default_factory=Proficiency)

class Strike(BaseModel):
    name: str
    attack_bonus: int
    damage_dice: str    # e.g., "1d8+4"
    damage_type: str    # e.g., "slashing"
    traits: List[str] = []

class Item(BaseModel):
    name: str
    category: str       # "weapon", "armor", "shield", "gear"
    bulk: str = "L"

class EquipmentLoadout(BaseModel):
    armor: Optional[Item] = None
    shield: Optional[Item] = None
    weapons: List[Item] = []
    gear: List[str] = []
    strikes: List[Strike] = []

class FeatSummary(BaseModel):
    id: str
    name: str
    category: str
    action_cost: Optional[int] = None
    description: str

class CharacterSheet(BaseModel):
    name: str
    level: int = 1
    ancestry: str
    background: str
    character_class: str
    size: str = "med"
    speed: int = 25
    attributes: AttributeModifiers
    defenses: Defenses
    perception: Proficiency
    trained_skills: List[str]
    equipment: EquipmentLoadout
    feats: List[FeatSummary] = []
    traits: List[str] = []
