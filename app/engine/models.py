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

class ConsumableItem(BaseModel):
    name: str
    quantity: int = 1
    item_type: str = "potion"
    bulk: Union[str, float, int] = "L"
    description: str = ""

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
    consumables: List[ConsumableItem] = []
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

class SpellSlotTracker(BaseModel):
    rank: int
    max_slots: int
    used_slots: int = 0

class SpellcastingData(BaseModel):
    tradition: str
    casting_attribute: str
    spell_dc: int
    spell_attack: int
    cantrips: List[SpellSummary] = []
    rank_1_spells: List[SpellSummary] = []
    rank_2_spells: List[SpellSummary] = []
    slots: List[SpellSlotTracker] = []

SpellcastingLoadout = SpellcastingData

class FocusSpellData(BaseModel):
    focus_points: int = 1
    max_focus_points: int = 1
    tradition: str = "Divine"
    casting_attribute: str = "CHA"
    spell_dc: int = 10
    spell_attack: int = 0
    spells: List[SpellSummary] = []

class PartnerCreatureData(BaseModel):
    name: str
    creature_type: str # "Animal Companion", "Eidolon", "Familiar", "Thrall / Minion"
    sub_type: str      # e.g., "Wolf", "Dragon Eidolon", "Raven Familiar"
    stage: str         # "Young", "Mature", "Standard"
    size: str
    speed: str
    ac: int
    hp: Union[int, str] # Supports integer HP or "Shared with Master"
    fortitude: int
    reflex: int
    will: int
    perception: int
    strikes: List[Strike] = []
    primary_ability: str # Support Benefit, Eidolon Feature, or Familiar Abilities
    secondary_ability: Optional[str] = None # Advanced Maneuver or Command Action
    traits: List[str] = []

AnimalCompanionData = PartnerCreatureData

class SubclassSummary(BaseModel):
    title: str
    name: str
    description: str

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
    heritage: Optional[str] = None
    background: str
    character_class: str
    subclass: Optional[SubclassSummary] = None
    archetype: Optional[str] = None
    size: str
    speed: int
    attributes: AttributeModifiers
    defenses: Defenses
    perception: Proficiency
    all_skills: List[SkillEntry] = []
    equipment: EquipmentLoadout
    spellcasting: Optional[SpellcastingData] = None
    focus_spells: Optional[FocusSpellData] = None
    companion: Optional[PartnerCreatureData] = None
    feats: List[FeatSummary] = []
    traits: List[str] = []
