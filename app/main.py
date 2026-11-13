from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.engine.archetypes import get_all_archetype_names
from app.engine.foundry import export_to_foundry_actor
from app.engine.generator import PF2eGenerator
from app.engine.subclasses import CLASS_SUBCLASSES
from backstory_generator import generate_epic_backstory

app = FastAPI(title="FastFinder PF2e Generator")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

generator = PF2eGenerator()


class LevelUpPayload(BaseModel):
    character: Dict[str, Any]
    target_level: int = Field(..., ge=1, le=20)
    use_dedication: bool = False
    archetype: Optional[str] = None


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/options")
def get_options():
    subclasses_by_class = {
        cls_k.lower(): [o["name"] for o in sub_info.get("options", [])]
        for cls_k, sub_info in CLASS_SUBCLASSES.items()
    }

    return {
        "ancestries": sorted([a["name"] for a in generator.ancestries.values()]),
        "classes": sorted([c["name"] for c in generator.classes.values()]),
        "backgrounds": sorted([b["name"] for b in generator.backgrounds.values()]),
        "archetypes": get_all_archetype_names(),
        "subclasses": subclasses_by_class,
    }


@app.get("/api/generate")
def generate_character(
    name: Optional[str] = None,
    ancestry: Optional[str] = None,
    class_name: Optional[str] = None,
    subclass: Optional[str] = None,
    background: Optional[str] = None,
    archetype: Optional[str] = None,
    level: int = Query(1, ge=1, le=20),
    dedication: bool = Query(False),
):
    try:
        clean_arch = (
            None
            if not archetype or archetype.lower() in ["any", "any archetype", "none"]
            else archetype.strip()
        )
        sheet = generator.generate(
            ancestry_name=ancestry,
            class_name=class_name,
            subclass_name=subclass,
            background_name=background,
            archetype_name=clean_arch,
            char_name=name,
            level=level,
            use_dedication=dedication or bool(clean_arch),
        )
        return sheet
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/epic-backstory")
def api_generate_backstory(character: dict):
    try:
        # Checks if generator has the method, otherwise uses a robust built-in fallback
        if hasattr(generator, "generate_epic_backstory"):
            chapters = generator.generate_epic_backstory(character)
        else:
            name = character.get("name") or "The Hero"
            ancestry = character.get("ancestry") or "Human"
            cls = character.get("character_class") or "Adventurer"
            lvl = character.get("level") or 1
            bg = character.get("background") or "unknown origins"
            
            chapters = [
                {
                    "chapter": "Chapter I: Roots in the Dust",
                    "narrative": f"Long before the weight of legendary arms rested upon {name}'s shoulders, there were quiet days spent as a {bg}. Raised amidst the rugged trials of the frontier, {name} learned early that survival is carved out of stubborn endurance rather than divine favor."
                },
                {
                    "chapter": "Chapter II: The Awakening Spark",
                    "narrative": f"As a {ancestry} navigating a world scarred by ancient powers, {name}'s path shifted when a latent calling took root. Stepping onto the path of the {cls}, every trial forged a sharper resolve, turning simple grit into legendary discipline."
                },
                {
                    "chapter": "Chapter III: The Legend at Zenith",
                    "narrative": f"Now standing at Level {lvl}, {name} is no longer merely a wanderer of the wilds. Bound to destiny and tested by insurmountable odds, their name echoes across the realm as a beacon of unyielding power and epic consequence."
                }
            ]
        return {"chapters": chapters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/levelup")
def level_up_endpoint(payload: LevelUpPayload):
    char_data = payload.character
    current_level = int(char_data.get("level", 1))
    target = max(1, min(20, int(payload.target_level)))

    if target == current_level:
        return char_data

    # Lock archetype
    existing_arch = char_data.get("archetype") or char_data.get("archetype_name")
    if isinstance(existing_arch, dict):
        existing_arch = existing_arch.get("name")

    if existing_arch and str(existing_arch).lower() not in ["", "none", "any", "any archetype"]:
        locked_arch = str(existing_arch).strip()
    else:
        req_arch = payload.archetype
        locked_arch = (
            None
            if not req_arch or req_arch.lower() in ["any", "any archetype", "none"]
            else req_arch.strip()
        )

    # In PF2e, dedication archetypes are level 2+ only
    use_ded = (payload.use_dedication or bool(locked_arch)) if target >= 2 else False

    try:
        updated_sheet = generator.level_up(
            char_data,
            target,
            use_dedication=use_ded,
            archetype_name=locked_arch,
        )
        return updated_sheet
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/foundry")
def export_foundry(
    name: Optional[str] = None,
    ancestry: Optional[str] = None,
    class_name: Optional[str] = None,
    subclass: Optional[str] = None,
    background: Optional[str] = None,
    archetype: Optional[str] = None,
    level: int = Query(1, ge=1, le=20),
    dedication: bool = Query(False),
):
    try:
        clean_arch = (
            None
            if not archetype or archetype.lower() in ["any", "any archetype", "none"]
            else archetype.strip()
        )
        sheet = generator.generate(
            ancestry_name=ancestry,
            class_name=class_name,
            subclass_name=subclass,
            background_name=background,
            archetype_name=clean_arch,
            char_name=name,
            level=level,
            use_dedication=dedication or bool(clean_arch),
        )
        foundry_actor = export_to_foundry_actor(sheet)

        # Handle both dict access and object attribute access safely
        char_name = getattr(sheet, "name", None) or (sheet.get("name") if isinstance(sheet, dict) else "character")
        filename = f"{char_name.lower().replace(' ', '_')}_foundry.json"

        return JSONResponse(
            content=foundry_actor,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
