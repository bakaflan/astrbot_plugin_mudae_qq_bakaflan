import json
import random
from pathlib import Path

class CharacterManager:
    """Encapsulates cached character data to avoid module-level globals."""

    def __init__(self) -> None:
        self._characters: list[dict] | None = None
        self._id_index: dict[int, dict] | None = None
        self._bonds: dict[str, list[int]] | None = None
        self._char_to_bonds: dict[int, list[str]] | None = None
        self._bond_boost_ratios: dict[str, list[float]] | None = None

    def load_characters(self) -> list[dict]:
        """Load pre-sorted character pool from file once."""
        if self._characters is None:
            data_path = Path(__file__).resolve().parent / "characters.json"
            try:
                with data_path.open("r", encoding="utf-8") as f:
                    self._characters = json.load(f)
            except FileNotFoundError:
                self._characters = []
            except json.JSONDecodeError as exc:
                self._characters = []
        if self._id_index is None:
            self._id_index = {
                c.get("id"): c
                for c in self._characters
                if isinstance(c, dict) and c.get("id") is not None
            }
        return self._characters

    def load_bonds(self) -> dict[str, list[int]]:
        if self._bonds is not None:
            return self._bonds
        data_path = Path(__file__).resolve().parent / "bonds.json"
        with data_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        self._bonds = {}
        self._bond_boost_ratios = {}
        for name, obj in raw.items():
            ids = obj.get("ids", [])
            self._bonds[name] = [int(x) for x in ids]
            self._bond_boost_ratios[name] = obj.get("boost_ratio", [1])
        self._char_to_bonds = {}
        for bond_name, ids in self._bonds.items():
            for cid in ids:
                self._char_to_bonds.setdefault(cid, []).append(bond_name)
        return self._bonds

    def get_bonds_for_character(self, character_id: int) -> list[str]:
        """Return bond names that include this character. Loads bonds on first use."""
        self.load_bonds()
        if self._char_to_bonds is None:
            return []
        return self._char_to_bonds.get(int(character_id), [])

    def get_boost_ratio(self, bond_name: str, owned_count: int) -> float:
        """Return boost ratio for a bond at given owned count. boost_ratio[i] is the ratio for i+1 owned (1st→index 0, 2nd→index 1, ...)."""
        self.load_bonds()
        ratios = (self._bond_boost_ratios or {}).get(bond_name, [1])
        if not ratios:
            return 1.0
        idx = min(max(0, owned_count - 1), len(ratios) - 1)
        return float(ratios[idx])

    def get_bond_collection_status(
        self, harem_ids: list[int] | list[str], only_with_owned: bool = True
    ) -> list[tuple[str, int, int, float, list[int]]]:
        self.load_bonds()
        if not self._bonds:
            return []
        harem_set = {int(x) for x in harem_ids}
        result = []
        for bond_name, member_ids in self._bonds.items():
            owned_cids = [cid for cid in member_ids if cid in harem_set]
            total = len(member_ids)
            owned = len(owned_cids)
            if only_with_owned and owned == 0:
                continue
            ratio = self.get_boost_ratio(bond_name, owned)
            result.append((bond_name, owned, total, ratio, owned_cids))
        return result

    def get_random_character(self, limit=None):
        """Return a random character dict, or None if pool empty."""
        chars = self.load_characters()
        if not chars:
            return None
        if limit:
            chars = chars[:limit]
        return random.choice(chars)

    def get_character_by_id(self, id):
        """O(1) lookup via cached id index; builds index on first use."""
        try:
            cid = int(id)
            if self._id_index is None:
                self.load_characters()
            return self._id_index.get(cid)
        except:
            return None

    def search_characters_by_name(self, keyword: str) -> list[dict]:
        """Return characters whose name contains the keyword (case-insensitive)."""
        if not keyword:
            return []
        key_lower = str(keyword).lower()
        chars = self.load_characters()
        if not chars:
            return []
        return [c for c in chars if key_lower in str(c.get("name", "")).lower()]

