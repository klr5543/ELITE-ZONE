import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()


class GameData:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self.items: Dict[str, Dict[str, Any]] = {}
        self._load_items()

    def _load_items(self) -> None:
        items_dir = self.base_path / "items"
        if not items_dir.is_dir():
            return
        for path in items_dir.glob("*.json"):
            try:
                with path.open(encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            item_id = str(data.get("id") or path.stem)
            self._index_item_key(item_id, data)
            name_value = data.get("name")
            if isinstance(name_value, dict):
                for value in name_value.values():
                    if isinstance(value, str):
                        self._index_item_key(value, data)
            elif isinstance(name_value, str):
                self._index_item_key(name_value, data)

    def _index_item_key(self, key: str, item: Dict[str, Any]) -> None:
        normalized = key.strip().lower()
        if not normalized:
            return
        if normalized in self.items:
            return
        self.items[normalized] = item

    def find_item(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        q = text.strip().lower()
        direct = self.items.get(q)
        if direct is not None:
            return direct
        best = None
        best_len = 0
        for key, item in self.items.items():
            if key in q and len(key) > best_len:
                best = item
                best_len = len(key)
        if best is not None:
            return best
        for key, item in self.items.items():
            if q in key:
                return item
        return None


def is_comparative_question(text: str) -> bool:
    lowered = text.lower()
    tokens = [
        " vs ",
        "vs ",
        " vs",
        " افضل ",
        "أفضل",
        "احسن",
        "أحسن",
        " or ",
        " or",
        "or ",
        "ولا",
        "مقارنة",
        "better",
        "best",
    ]
    return any(token in lowered for token in tokens)


def is_strategy_question(text: str) -> bool:
    lowered = text.lower()
    tokens = [
        "استراتيجية",
        "strategy",
        "كيف العب",
        "كيف ألعب",
        "كيف العب؟",
        "كيف ألعب؟",
        "build",
        "بيلد",
        "meta",
        "ميتا",
        "طريقة اللعب",
    ]
    return any(token in lowered for token in tokens)


def is_explanatory_question(text: str) -> bool:
    lowered = text.lower()
    tokens = [
        "ليش",
        "لماذا",
        "why",
        "سبب",
        "اشرح",
        "شرح",
        "explain",
    ]
    return any(token in lowered for token in tokens)


def should_use_ai(text: str) -> bool:
    if is_comparative_question(text):
        return True
    if is_strategy_question(text):
        return True
    if is_explanatory_question(text):
        return True
    return False


def format_item_answer(item: Dict[str, Any]) -> str:
    name_value = item.get("name")
    description_value = item.get("description")
    name_text = None
    if isinstance(name_value, dict):
        name_text = name_value.get("en")
        if not name_text and name_value:
            name_text = next((v for v in name_value.values() if isinstance(v, str)), None)
    elif isinstance(name_value, str):
        name_text = name_value
    description_text = None
    if isinstance(description_value, dict):
        description_text = description_value.get("en")
        if not description_text and description_value:
            description_text = next(
                (v for v in description_value.values() if isinstance(v, str)),
                None,
            )
    elif isinstance(description_value, str):
        description_text = description_value
    item_type = item.get("type") or "-"
    rarity = item.get("rarity") or "-"
    weight = item.get("weightKg")
    parts = []
    if name_text:
        parts.append(f"الاسم: {name_text}")
    parts.append(f"النوع: {item_type}")
    parts.append(f"الندرة: {rarity}")
    if weight is not None:
        parts.append(f"الوزن: {weight} كجم")
    if description_text:
        parts.append(f"الوصف (من داتا اللعبة): {description_text}")
    return "\n".join(parts)


async def generate_ai_answer(
    question: str, item: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    endpoint = os.getenv("AI_ENDPOINT")
    api_key = os.getenv("AI_API_KEY")
    model = os.getenv("AI_MODEL")
    if not endpoint or not api_key or not model:
        return None
    system_prompt = (
        "You are an assistant for the ARC Raiders game. "
        "Answer briefly and directly. "
        "If the user writes in Arabic, answer in Arabic. "
        "Use structured game data as ground truth when possible."
    )
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    }
    if item is not None:
        payload["context"] = {"item": item}
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            async with session.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=20,
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except Exception:
        return None
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
    return None


base_dir = Path(__file__).resolve().parent
game_data = GameData(base_dir / "arcraiders-data")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready() -> None:
    guilds = ", ".join(g.name for g in bot.guilds)
    print(f"Logged in as {bot.user} in: {guilds}")


async def handle_question_message(message: discord.Message) -> None:
    content = message.content.strip()
    if not content:
        return
    use_ai = should_use_ai(content)
    item = game_data.find_item(content)
    if item is not None and not use_ai:
        answer = format_item_answer(item)
        await message.channel.send(answer)
        return
    if use_ai:
        ai_answer = await generate_ai_answer(content, item)
        if ai_answer:
            await message.channel.send(ai_answer)
            return
        await message.channel.send(
            "هذا سؤال مركّب ويحتاج AI، لكن تكامل الذكاء الاصطناعي غير مفعّل حالياً."
        )
        return
    await message.channel.send(
        "ما لقيت شيء واضح في داتا اللعبة يطابق سؤالك.\n"
        "جرّب تكتب اسم الآيتم مباشرة أو استخدم الأمر: !item اسم_الآيتم"
    )


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return
    channel_id_str = os.getenv("QUESTION_CHANNEL_ID")
    if channel_id_str:
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            channel_id = None
        if channel_id is not None and message.channel.id != channel_id:
            await bot.process_commands(message)
            return
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return
    await handle_question_message(message)
    await bot.process_commands(message)


@bot.command(name="item")
async def item_command(ctx: commands.Context, *, query: str) -> None:
    item = game_data.find_item(query)
    if item is None:
        await ctx.reply(
            "ما لقيت هذا الآيتم في داتا ARC Raiders.",
            mention_author=False,
        )
        return
    answer = format_item_answer(item)
    await ctx.reply(answer, mention_author=False)


def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is not set")
    bot.run(token)


if __name__ == "__main__":
    main()
