import random

def generate_epic_backstory(char_data: dict) -> list:
    name = char_data.get("name") or "The Hero"
    ancestry = char_data.get("ancestry") or "Human"
    cls = char_data.get("character_class") or "Adventurer"
    lvl = int(char_data.get("level") or 1)
    bg = char_data.get("background") or "unknown origins"
    
    # Fully randomized sentence collections with zero shared phrasing templates
    ch1_options = [
        f"Before {name} ever touched a blade, their life was dictated by the grueling manual demands of a {bg}. Days bled together in an endless cycle of sweat and quiet labor, far away from any bard's ballad.",
        f"Long before destiny came knocking, {name} spent their formative years navigating the harsh realities of a {bg}. It was an unglamorous, backbreaking education that forged their underlying toughness.",
        f"The early chapters of {name}'s story were written in the dirt and routine of a {bg}. Without the safety nets of fortune, they learned how to outlast misfortune through sheer stubborn persistence.",
        f"Every calloused hand and hardened look {name} carried was earned during their time as a {bg}. Those quiet, grueling days built an absolute foundation of self-reliance."
    ]

    ch2_options = [
        f"Bloodlines and ambition collided the day {name}, a resolute {ancestry}, decided to abandon the familiar. Stepping onto the perilous path of the {cls}, they began mastering disciplines that ordinary mortals fear.",
        f"The traditions of a {ancestry} run deep, but {name}'s path fractured permanently when they embraced the mantle of a {cls}. Every trial since has turned raw, unrefined potential into razor-sharp focus.",
        f"Though born to the proud heritage of a {ancestry}, {name} was never meant for a quiet life. Plunging headfirst into the rigorous training of a {cls}, they forged an entirely new identity from the chaos.",
        f"An unexpected catalyst upended everything {name} thought they knew. Drawing deep strength from their {ancestry} roots, they swore themselves to the demanding lifestyle of a {cls}."
    ]

    if lvl <= 2:
        ch3_options = [
            f"Now taking their very first cautious breaths as a Level {lvl} {cls}, {name} stands at the absolute threshold of a dangerous world, armed with little more than nerve and resolve.",
            f"At Level {lvl}, {name} is a newcomer facing an unpredictable horizon, leaving the safety of the past behind as they test their mettle as a {cls}."
        ]
    elif lvl <= 6:
        ch3_options = [
            f"Having survived the brutal filtration of the early road, {name} now commands respect as a capable Level {lvl} {cls}, their early blunders replaced by a growing reputation.",
            f"Standing tall at Level {lvl}[cite: 8], {name} has proven their worth as a {cls}, drawing the watchful eyes of frontier outposts and regional travelers alike."
        ]
    elif lvl <= 14:
        ch3_options = [
            f"Now a hardened veteran operating at Level {lvl}, {name}'s exploits as a {cls} send ripples across provincial borders, forcing regional powers to keep a close eye on their moves.",
            f"Moving through the world as an established {cls} at Level {lvl}, {name} commands influence and shapes the local tides of danger and politics."
        ]
    else:
        ch3_options = [
            f"Standing at the absolute zenith of mortal power at Level {lvl}, {name} has transcended ordinary adventure to become a living legend, their ongoing saga bending the history of the realm.",
            f"At Level {lvl}, {name} commands awe across empires, their epic feats as a {cls} echoing through the ages like a true force of nature."
        ]

    return [
        {"chapter": "Chapter I: Roots and Reality", "narrative": random.choice(ch1_options)},
        {"chapter": "Chapter II: The Turning Point", "narrative": random.choice(ch2_options)},
        {"chapter": "Chapter III: The Road Ahead", "narrative": random.choice(ch3_options)}
    ]
