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

class SkillEntry(BaseModel):
    name: str
    attribute: str      # e.g., "dex", "int"
    rank: int = 2       # Remaster Trained = 2
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
    damage_dice: str
    damage_type: str
    traits: List[str] = []

class Item(BaseModel):
    name: str
    category: str
    bulk: str = "L"

class EquipmentLoadout(BaseModel):
    armor: Optional[Item] = None
    shield: Optional[Item] = None
    weapons: List[Item] = []
    gear: List[str] = []
    strikes: List[Strike] = []

class SpellEntry(BaseModel):
    name: str
    rank: int               # 0 = Cantrip, 1 = Rank 1
    actions: str = "2 actions"
    range: str = "30 feet"
    summary: str
    traits: List[str] = []

class SpellcastingLoadout(BaseModel):
    tradition: str          # "Arcane", "Divine", "Occult", "Primal"
    casting_attribute: str  # "int", "wis", "cha"
    spell_dc: int
    spell_attack: int
    cantrips: List[SpellEntry] = []
    rank_1_spells: List[SpellEntry] = []

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
    trained_skills: List[SkillEntry]
    equipment: EquipmentLoadout
    spellcasting: Optional[SpellcastingLoadout] = None
    feats: List[FeatSummary] = []
    traits: List[str] = []
