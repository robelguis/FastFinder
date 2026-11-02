from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class AttributeModifiers(BaseModel):
    strength: int = Field(..., alias="str")
    dexterity: int = Field(..., alias="dex")
    constitution: int = Field(..., alias="con")
    intelligence: int = Field(..., alias="int")
    wisdom: int = Field(..., alias="wis")
    charisma: int = Field(..., alias="cha")

    class Config:
        populate_by_name = True

class Proficiency(BaseModel):
    rank: int          # 0=Untrained, 2=Trained, 4=Expert, 6=Master, 8=Legendary
    rank_letter: str   # U, T, E, M, L
    modifier: int

class Defenses(BaseModel):
    ac: int
    shield_bonus: int = 0
    hp: int
    fortitude: Proficiency
    reflex: Proficiency
    will: Proficiency

class SkillEntry(BaseModel):
    name: str
    attribute: str
    rank: int
    rank_letter: str
    modifier: int

class Strike(BaseModel):
    name: str
    attack_bonus: int
    map_second: int
    map_third: int
    damage_dice: str
    damage_type: str
    traits: List[str] = []

StrikeOption = Strike

class Item(BaseModel):
    name: str
    bulk: Union[str, float, int] = "0"
    cost_sp: Optional[int] = 0

ItemEntry = Item

class Wealth(BaseModel):
    pp: int = 0
    gp: int = 0
    sp: int = 0
    cp: int = 0
    formatted: str = ""

CurrencyPurse = Wealth

class EquipmentLoadout(BaseModel):
    weapons: List[Item] = []
    armor: Optional[Item] = None
    shield: Optional[Item] = None
    gear: List[str] = []
    money: Wealth = Wealth()
    strikes: List[Strike] = []

class SpellSummary(BaseModel):
    name: str
    rank: int
    actions: str
    traits: List[str] = []
    range: Optional[str] = None
    targets: Optional[str] = None
    defense: Optional[str] = None
    description: str

SpellEntry = SpellSummary

class SpellcastingData(BaseModel):
    tradition: str
    casting_attribute: str
    spell_dc: int
    spell_attack: int
    cantrips: List[SpellSummary] = []
    rank_1_spells: List[SpellSummary] = []

SpellcastingLoadout = SpellcastingData

class FeatSummary(BaseModel):
    id: str
    name: str
    category: str
    action_cost: Optional[int] = None
    traits: List[str] = []
    description: str

class CharacterSheet(BaseModel):
    name: str
    level: int = 1
    ancestry: str
    background: str
    character_class: str
    size: str
    speed: int
    attributes: AttributeModifiers
    defenses: Defenses
    perception: Proficiency
    all_skills: List[SkillEntry] = []
    equipment: EquipmentLoadout
    spellcasting: Optional[SpellcastingData] = None
    feats: List[FeatSummary] = []
    traits: List[str] = []
