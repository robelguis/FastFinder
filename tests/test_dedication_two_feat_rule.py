from app.engine.generator import can_take_dedication
from app.engine.models import FeatSummary


def _feat(name: str, category: str, traits: list[str]) -> FeatSummary:
    return FeatSummary(
        id=name.lower().replace(" ", "-"),
        name=name,
        category=category,
        traits=traits,
        description="",
    )


def test_first_dedication_allowed_when_none_taken():
    assert can_take_dedication("Marshal Dedication", [], set()) is True


def test_duplicate_dedication_blocked():
    marshal_ded = _feat("Marshal Dedication", "Archetype (Marshal)", ["archetype", "dedication"])
    assert can_take_dedication("Marshal Dedication", [marshal_ded], {"Marshal Dedication"}) is False


def test_second_dedication_requires_two_other_feats_from_same_archetype():
    marshal_ded = _feat("Marshal Dedication", "Archetype (Marshal)", ["archetype", "dedication"])
    marshal_f1 = _feat("Rallying Charge", "Archetype (Marshal)", ["archetype", "marshal"])
    marshal_f2 = _feat("Back to Back", "Archetype (Marshal)", ["archetype", "marshal"])
    unrelated_arch = _feat("Medic Dedication", "Archetype (Medic)", ["archetype", "dedication"])

    # 0 non-dedication Marshal feats -> blocked
    assert can_take_dedication("Bastion Dedication", [marshal_ded], {"Marshal Dedication"}) is False

    # 1 non-dedication Marshal feat -> still blocked
    assert can_take_dedication(
        "Bastion Dedication",
        [marshal_ded, marshal_f1],
        {"Marshal Dedication", "Rallying Charge"},
    ) is False

    # Unrelated dedication feat must not count toward the 2-feat prerequisite
    assert can_take_dedication(
        "Bastion Dedication",
        [marshal_ded, marshal_f1, unrelated_arch],
        {"Marshal Dedication", "Rallying Charge", "Medic Dedication"},
    ) is False

    # 2 non-dedication Marshal feats -> allowed
    assert can_take_dedication(
        "Bastion Dedication",
        [marshal_ded, marshal_f1, marshal_f2],
        {"Marshal Dedication", "Rallying Charge", "Back to Back"},
    ) is True


def test_chained_dedications_check_most_recent_archetype():
    marshal_ded = _feat("Marshal Dedication", "Archetype (Marshal)", ["archetype", "dedication"])
    marshal_f1 = _feat("Rallying Charge", "Archetype (Marshal)", ["archetype", "marshal"])
    marshal_f2 = _feat("Back to Back", "Archetype (Marshal)", ["archetype", "marshal"])
    bastion_ded = _feat("Bastion Dedication", "Archetype (Bastion)", ["archetype", "dedication"])
    bastion_f1 = _feat("Disarming Block", "Archetype (Bastion)", ["archetype", "bastion"])
    bastion_f2 = _feat("Reflexive Shield", "Archetype (Bastion)", ["archetype", "bastion"])

    feats_with_one_bastion = [marshal_ded, marshal_f1, marshal_f2, bastion_ded, bastion_f1]
    names_one = {f.name for f in feats_with_one_bastion}
    assert can_take_dedication("Sentinel Dedication", feats_with_one_bastion, names_one) is False

    feats_with_two_bastion = feats_with_one_bastion + [bastion_f2]
    names_two = {f.name for f in feats_with_two_bastion}
    assert can_take_dedication("Sentinel Dedication", feats_with_two_bastion, names_two) is True
