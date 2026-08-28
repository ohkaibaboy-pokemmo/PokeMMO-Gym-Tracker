from dataclasses import dataclass
import tkinter as tk


PORTRAIT_SIZE = 36


@dataclass(frozen=True)
class LeaderProfile:
    hair: str
    outfit: str
    accent: str
    skin: str = "#e7b98d"
    style: str = "short"
    accessory: str = ""
    eye: str = "#20242a"


# Original miniature portraits. The palettes/cues identify the leader without
# copying any game sprite pixels or bundling third-party artwork.
LEADER_PROFILES = {
    # Kanto
    "Brock": LeaderProfile("#4b3427", "#c8813d", "#7a5836", style="spiky", skin="#b98361"),
    "Misty": LeaderProfile("#e7782f", "#f2cc43", "#d95d3b", style="ponytail"),
    "Lt. Surge": LeaderProfile("#e6cf62", "#6d8b4f", "#b5a758", style="spiky", accessory="shades"),
    "Erika": LeaderProfile("#302c2a", "#b64d43", "#e0ba50", style="bob", accessory="flower"),
    "Koga": LeaderProfile("#38313e", "#5b466e", "#98638c", style="hood", accessory="mask"),
    "Sabrina": LeaderProfile("#252329", "#a53d45", "#c86f66", style="long"),
    "Blaine": LeaderProfile("#d6d3cc", "#b83c35", "#e3c45b", style="bald", accessory="glasses"),
    # Johto
    "Falkner": LeaderProfile("#4f6c8b", "#557ca0", "#d5dbe5", style="swept"),
    "Bugsy": LeaderProfile("#8f789b", "#7d8b55", "#d8c964", style="bob"),
    "Whitney": LeaderProfile("#d98ca7", "#ead2df", "#bb577c", style="ponytail"),
    "Morty": LeaderProfile("#d2b26a", "#67507c", "#8c6fa1", style="swept", accessory="headband"),
    "Chuck": LeaderProfile("#2b2a2c", "#4c6e8e", "#d46a4b", style="short", skin="#c98f66"),
    "Jasmine": LeaderProfile("#6b4d38", "#e8e7df", "#b8c5d6", style="long", accessory="clips"),
    "Pryce": LeaderProfile("#d8d8d2", "#687e8a", "#a8c2cb", style="short", accessory="brows", skin="#d6a982"),
    "Clair": LeaderProfile("#526a98", "#6a5e8f", "#b9a9d4", style="ponytail"),
    # Hoenn
    "Roxanne": LeaderProfile("#5a4439", "#7e5d65", "#d3c1b0", style="long", accessory="ribbon"),
    "Brawly": LeaderProfile("#4b78a3", "#e07d45", "#5ba2b5", style="spiky", skin="#c88b60"),
    "Wattson": LeaderProfile("#d4d2c6", "#b29a45", "#6c7f4c", style="fluffy", accessory="moustache", skin="#c9966e"),
    "Flannery": LeaderProfile("#bd4d37", "#3b3940", "#e66f48", style="spiky", accessory="headband"),
    "Norman": LeaderProfile("#56443d", "#6f7f8e", "#b05c4b", style="short", skin="#c68f6a"),
    "Winona": LeaderProfile("#77609a", "#7190a5", "#d3d8e2", style="long", accessory="wing"),
    "Tate & Liza": LeaderProfile("#aa5d66", "#667da6", "#d8a65e", style="duo"),
    "Juan": LeaderProfile("#6a6373", "#426f8b", "#76a9bd", style="swept", accessory="moustache", skin="#bf8967"),
    # Sinnoh
    "Roark": LeaderProfile("#7b4a35", "#77706b", "#d4553c", style="short", accessory="hardhat"),
    "Gardenia": LeaderProfile("#5f4938", "#758b45", "#e3c05c", style="bob", accessory="leaf"),
    "Maylene": LeaderProfile("#b36f8d", "#7e78a0", "#d7a1b8", style="short"),
    "Crasher Wake": LeaderProfile("#3e6b91", "#345a80", "#e7c24e", style="bald", accessory="mask", skin="#bf865f"),
    "Fantina": LeaderProfile("#654a7a", "#9b678f", "#d8abc6", style="fluffy", accessory="bow"),
    "Byron": LeaderProfile("#6a625b", "#596777", "#9d6e43", style="short", accessory="brows", skin="#bb8562"),
    "Candice": LeaderProfile("#4b4b52", "#5e8aa5", "#d5edf2", style="long", accessory="scarf"),
    "Volkner": LeaderProfile("#d8bd54", "#6f7781", "#6ea0b1", style="spiky"),
    # Unova
    "Cilan": LeaderProfile("#6b9b54", "#e6e2d7", "#8caf66", style="swept", accessory="bowtie"),
    "Chili": LeaderProfile("#b84e3e", "#e5e0d8", "#d96d47", style="spiky", accessory="bowtie"),
    "Cress": LeaderProfile("#507ca7", "#e6e2d8", "#73a1c1", style="swept", accessory="bowtie"),
    "Lenora": LeaderProfile("#5a4337", "#b68b58", "#5b79a0", style="fluffy", accessory="glasses", skin="#8f6046"),
    "Burgh": LeaderProfile("#a78a55", "#648a5a", "#d19b4c", style="swept"),
    "Elesa": LeaderProfile("#e0cc6e", "#3f4249", "#55a7a3", style="long", accessory="headphones"),
    "Clay": LeaderProfile("#5e4636", "#806045", "#c59b54", style="short", accessory="cowboy", skin="#b77c56"),
    "Skyla": LeaderProfile("#a65845", "#5892ac", "#d9e7e8", style="ponytail", accessory="goggles"),
    "Brycen": LeaderProfile("#56728c", "#657e91", "#b8d1da", style="short", accessory="mask"),
    "Iris": LeaderProfile("#5c486d", "#e5d8cc", "#bd78a8", style="twin", skin="#9b684c"),
}


class PixelPortraitRenderer:
    def __init__(self, master, theme):
        self.master = master
        self.theme = theme

    def render(self, leader):
        profile = LEADER_PROFILES.get(leader)
        if profile is None:
            profile = LeaderProfile("#666666", "#777777", "#999999")
        if profile.style == "duo":
            return self._render_duo(profile)

        image = self._canvas()
        self._draw_body(image, profile)
        self._draw_face(image, profile)
        self._draw_hair(image, profile)
        self._draw_features(image, profile)
        self._draw_accessory(image, profile)
        return image

    def _canvas(self):
        image = tk.PhotoImage(master=self.master, width=PORTRAIT_SIZE, height=PORTRAIT_SIZE)
        image.put(self.theme["panel"], to=(0, 0, PORTRAIT_SIZE, PORTRAIT_SIZE))
        image.put(self.theme["heading"], to=(1, 1, PORTRAIT_SIZE - 1, PORTRAIT_SIZE - 1))
        image.put(self.theme["panel_dark"], to=(3, 3, PORTRAIT_SIZE - 3, PORTRAIT_SIZE - 3))
        return image

    @staticmethod
    def _rect(image, colour, x1, y1, x2, y2):
        image.put(colour, to=(x1, y1, x2, y2))

    def _draw_body(self, image, p):
        self._rect(image, p.outfit, 7, 26, 29, 34)
        self._rect(image, p.accent, 11, 26, 25, 29)
        self._rect(image, p.skin, 15, 23, 21, 27)

    def _draw_face(self, image, p):
        outline = "#2b2728"
        self._rect(image, outline, 9, 9, 27, 23)
        self._rect(image, p.skin, 10, 10, 26, 22)
        self._rect(image, p.skin, 8, 14, 10, 19)
        self._rect(image, p.skin, 26, 14, 28, 19)

    def _draw_hair(self, image, p):
        c = p.hair
        style = p.style
        if style == "bald":
            self._rect(image, c, 11, 8, 25, 10)
            return
        if style == "spiky":
            self._rect(image, c, 9, 7, 27, 12)
            for x in (9, 13, 18, 23):
                self._rect(image, c, x, 5 + (x % 3), x + 3, 9)
            self._rect(image, c, 8, 10, 11, 17)
            self._rect(image, c, 25, 10, 28, 17)
        elif style == "long":
            self._rect(image, c, 9, 6, 27, 12)
            self._rect(image, c, 7, 9, 11, 26)
            self._rect(image, c, 25, 9, 29, 26)
        elif style == "bob":
            self._rect(image, c, 8, 7, 28, 13)
            self._rect(image, c, 7, 11, 11, 22)
            self._rect(image, c, 25, 11, 29, 22)
        elif style == "ponytail":
            self._rect(image, c, 9, 7, 27, 12)
            self._rect(image, c, 8, 10, 11, 18)
            self._rect(image, c, 26, 9, 30, 14)
            self._rect(image, c, 29, 11, 32, 21)
        elif style == "twin":
            self._rect(image, c, 9, 6, 27, 12)
            self._rect(image, c, 5, 8, 10, 19)
            self._rect(image, c, 26, 8, 31, 19)
            self._rect(image, c, 4, 16, 8, 25)
            self._rect(image, c, 28, 16, 32, 25)
        elif style == "hood":
            self._rect(image, c, 7, 6, 29, 12)
            self._rect(image, c, 6, 10, 11, 25)
            self._rect(image, c, 25, 10, 30, 25)
        elif style == "fluffy":
            for box in ((9, 5, 15, 10), (14, 4, 22, 9), (21, 6, 28, 11), (7, 9, 12, 17), (25, 9, 30, 18)):
                self._rect(image, c, *box)
        elif style == "swept":
            self._rect(image, c, 9, 6, 27, 12)
            self._rect(image, c, 7, 9, 14, 15)
            self._rect(image, c, 22, 8, 29, 12)
        else:
            self._rect(image, c, 9, 7, 27, 12)
            self._rect(image, c, 8, 10, 11, 16)
            self._rect(image, c, 25, 10, 28, 16)

    def _draw_features(self, image, p):
        eye = p.eye
        self._rect(image, eye, 13, 15, 15, 17)
        self._rect(image, eye, 21, 15, 23, 17)
        self._rect(image, "#9b5c54", 16, 20, 20, 21)

    def _draw_accessory(self, image, p):
        a = p.accessory
        if not a:
            return
        dark = "#25272b"
        if a in {"glasses", "shades"}:
            colour = dark if a == "shades" else p.accent
            self._rect(image, colour, 11, 14, 16, 18)
            self._rect(image, colour, 20, 14, 25, 18)
            self._rect(image, colour, 16, 15, 20, 16)
        elif a == "mask":
            self._rect(image, p.accent, 10, 14, 26, 20)
            self._rect(image, dark, 13, 15, 15, 17)
            self._rect(image, dark, 21, 15, 23, 17)
        elif a == "headband":
            self._rect(image, p.accent, 8, 9, 28, 12)
        elif a == "flower":
            for box in ((24, 7, 27, 10), (27, 8, 30, 11), (25, 10, 28, 13)):
                self._rect(image, p.accent, *box)
        elif a == "clips":
            self._rect(image, p.accent, 8, 10, 11, 13)
            self._rect(image, p.accent, 25, 10, 28, 13)
        elif a == "ribbon":
            self._rect(image, p.accent, 7, 7, 12, 10)
            self._rect(image, p.accent, 24, 7, 29, 10)
        elif a == "hardhat":
            self._rect(image, p.accent, 8, 5, 28, 10)
            self._rect(image, p.outfit, 11, 4, 25, 7)
        elif a == "cowboy":
            self._rect(image, p.accent, 6, 5, 30, 8)
            self._rect(image, p.outfit, 11, 2, 25, 7)
        elif a == "goggles":
            self._rect(image, dark, 11, 6, 16, 9)
            self._rect(image, dark, 20, 6, 25, 9)
            self._rect(image, p.accent, 16, 7, 20, 8)
        elif a == "headphones":
            self._rect(image, p.accent, 6, 11, 10, 20)
            self._rect(image, p.accent, 26, 11, 30, 20)
            self._rect(image, p.accent, 9, 6, 27, 8)
        elif a == "moustache":
            self._rect(image, p.hair, 13, 19, 18, 21)
            self._rect(image, p.hair, 18, 19, 23, 21)
        elif a == "brows":
            self._rect(image, p.hair, 12, 13, 16, 14)
            self._rect(image, p.hair, 20, 13, 24, 14)
        elif a == "leaf":
            self._rect(image, p.accent, 25, 6, 29, 10)
            self._rect(image, p.accent, 27, 4, 30, 8)
        elif a == "bow":
            self._rect(image, p.accent, 7, 7, 12, 11)
            self._rect(image, p.accent, 12, 8, 15, 10)
        elif a == "scarf":
            self._rect(image, p.accent, 10, 24, 26, 28)
        elif a == "wing":
            self._rect(image, p.accent, 5, 8, 9, 15)
            self._rect(image, p.accent, 27, 8, 31, 15)
        elif a == "bowtie":
            self._rect(image, p.accent, 12, 25, 17, 29)
            self._rect(image, p.accent, 19, 25, 24, 29)
            self._rect(image, dark, 17, 26, 19, 28)

    def _render_duo(self, p):
        image = self._canvas()
        # Two deliberately tiny mirrored faces for Tate & Liza.
        self._rect(image, p.outfit, 4, 25, 32, 34)
        for offset, hair in ((0, p.hair), (16, p.accent)):
            self._rect(image, "#2b2728", 3 + offset, 9, 18 + offset, 23)
            self._rect(image, p.skin, 4 + offset, 10, 17 + offset, 22)
            self._rect(image, hair, 3 + offset, 6, 18 + offset, 12)
            self._rect(image, "#25272b", 8 + offset, 15, 10 + offset, 17)
            self._rect(image, "#25272b", 13 + offset, 15, 15 + offset, 17)
        self._rect(image, p.accent, 14, 25, 22, 29)
        return image
