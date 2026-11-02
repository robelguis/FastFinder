import random
from typing import Tuple, List
from app.engine.models import Item, Strike, EquipmentLoadout, Wealth, ConsumableItem

def resolve_equipment(class_name: str, str_mod: int, dex_mod: int, level: int = 1) -> Tuple[EquipmentLoadout, int, int]:
    cls = class_name.lower()

    # Default starting weapons
    strikes: List[Strike] = []
    weapons: List[Item] = []
    armor: Item = None
    shield: Item = None
    shield_bonus = 0

    # Consumables assignment
    consumables: List[ConsumableItem] = [
        ConsumableItem(
            name="Minor Healing Potion",
            quantity=1 if level == 1 else 2,
            item_type="potion",
            bulk="L",
            description="Drink to restore 1d8 Hit Points (1 Action)."
        )
    ]

    if cls in ["alchemist"]:
        consumables.append(
            ConsumableItem(
                name="Lesser Elixir of Life",
                quantity=2,
                item_type="elixir",
                bulk="L",
                description="Drink to restore 1d6 Hit Points and gain +1 item bonus to saves vs poison/disease for 10 min."
            )
        )
        consumables.append(
            ConsumableItem(
                name="Lesser Acid Flask",
                quantity=2,
                item_type="alchemical",
                bulk="L",
                description="Thrown bomb dealing 1 persistent acid damage plus 1 acid splash."
            )
        )

    # Martial vs Caster loadouts
    if cls in ["fighter", "champion"]:
        weapons.append(Item(name="Longsword", bulk=1, cost_sp=10))
        strikes.append(Strike(
            name="Longsword",
            attack_bonus=str_mod + 4 + level, # Fighter master/expert track
            map_second=(str_mod + 4 + level) - 5,
            map_third=(str_mod + 4 + level) - 10,
            damage_dice=f"1d8+{str_mod}",
            damage_type="Slashing",
            traits=["Versatile P"]
        ))
        armor = Item(name="Breastplate", bulk=2, cost_sp=80)
        shield = Item(name="Steel Shield", bulk=1, cost_sp=20)
        shield_bonus = 2
        base_ac = 10 + 4 + dex_mod if dex_mod <= 1 else 10 + 4 + 1
        ac = base_ac + 2 + level

    elif cls in ["rogue", "swashbuckler", "investigator"]:
        weapons.append(Item(name="Rapier", bulk=1, cost_sp=15))
        weapons.append(Item(name="Dagger", bulk="L", cost_sp=2))
        strikes.append(Strike(
            name="Rapier",
            attack_bonus=dex_mod + 2 + level,
            map_second=(dex_mod + 2 + level) - 5,
            map_third=(dex_mod + 2 + level) - 10,
            damage_dice=f"1d6+{str_mod}",
            damage_type="Piercing",
            traits=["Deadly d8", "Disarm", "Finesse"]
        ))
        strikes.append(Strike(
            name="Dagger",
            attack_bonus=dex_mod + 2 + level,
            map_second=(dex_mod + 2 + level) - 4,
            map_third=(dex_mod + 2 + level) - 8,
            damage_dice=f"1d4+{str_mod}",
            damage_type="Piercing",
            traits=["Agile", "Finesse", "Thrown 10ft", "Versatile S"]
        ))
        armor = Item(name="Leather Armor", bulk=1, cost_sp=20)
        ac = 10 + 1 + min(dex_mod, 4) + 2 + level

    elif cls in ["barbarian"]:
        weapons.append(Item(name="Greataxe", bulk=2, cost_sp=20))
        strikes.append(Strike(
            name="Greataxe",
            attack_bonus=str_mod + 2 + level,
            map_second=(str_mod + 2 + level) - 5,
            map_third=(str_mod + 2 + level) - 10,
            damage_dice=f"1d12+{str_mod}",
            damage_type="Slashing",
            traits=["Sweep"]
        ))
        armor = Item(name="Hide Armor", bulk=2, cost_sp=20)
        ac = 10 + 3 + min(dex_mod, 2) + 2 + level

    elif cls in ["ranger", "gunslinger"]:
        weapons.append(Item(name="Composite Shortbow", bulk=1, cost_sp=70))
        strikes.append(Strike(
            name="Composite Shortbow",
            attack_bonus=dex_mod + 2 + level,
            map_second=(dex_mod + 2 + level) - 5,
            map_third=(dex_mod + 2 + level) - 10,
            damage_dice=f"1d6+{max(0, str_mod // 2)}",
            damage_type="Piercing",
            traits=["Deadly d10", "Propulsive", "Range 60ft"]
        ))
        armor = Item(name="Leather Armor", bulk=1, cost_sp=20)
        ac = 10 + 1 + min(dex_mod, 4) + 2 + level

    else:
        # Default caster / standard loadout
        weapons.append(Item(name="Staff", bulk=1, cost_sp=0))
        strikes.append(Strike(
            name="Staff",
            attack_bonus=str_mod + 2 + level,
            map_second=(str_mod + 2 + level) - 5,
            map_third=(str_mod + 2 + level) - 10,
            damage_dice=f"1d4+{str_mod}",
            damage_type="Bludgeoning",
            traits=["Two-Hand d8"]
        ))
        armor = Item(name="Explorer's Clothing", bulk=0, cost_sp=1)
        ac = 10 + dex_mod + 2 + level

    gear_items = ["Backpack", "Bedroll", "Rations (1 week)", "Waterskin", "Torch (5)", "Flint and Steel", "50ft Rope"]
    wealth = Wealth(gp=random.randint(2, 6), sp=random.randint(1, 9), cp=random.randint(0, 9))
    wealth.formatted = f"{wealth.gp} GP, {wealth.sp} SP, {wealth.cp} CP"

    loadout = EquipmentLoadout(
        weapons=weapons,
        armor=armor,
        shield=shield,
        gear=gear_items,
        consumables=consumables,
        money=wealth,
        strikes=strikes
    )

    return loadout, ac, shield_bonus
